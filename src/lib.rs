use pyo3::prelude::*;

pub mod built_info {
    include!(concat!(env!("OUT_DIR"), "/built.rs"));
}

/// Very fast, constant memory-footprint cardinality approximation, including intersection and union operation.
#[pyclass]
struct Sketch {
    inner: hyperminhash::Sketch,
}

#[pymethods]
impl Sketch {
    #[new]
    fn new() -> Self {
        Self {
            inner: Default::default(),
        }
    }

    /// Deserialize an instance from a buffer given by `Sketch.save()`
    #[staticmethod]
    fn load(buf: &[u8]) -> PyResult<Self> {
        Ok(Self {
            inner: hyperminhash::Sketch::load(buf)?,
        })
    }

    #[staticmethod]
    /// Construct a new Sketch from an iterator of objects
    fn from_iter(py: Python, mut iter: &pyo3::types::PyIterator) -> PyResult<Self> {
        let mut sk = hyperminhash::Sketch::default();
        loop {
            // SAFETY: We never observe `obj` after hashing it
            let pool = unsafe { py.new_pool() };
            match iter.next() {
                Some(obj) => {
                    obj?.hash().map(|h| sk.add(h))?;
                }
                None => {
                    break;
                }
            }
            drop(pool);
        }
        Ok(Self { inner: sk })
    }

    #[staticmethod]
    /// Construct a new Sketch from an iterator of bytes-objects
    fn from_iter_bytes(py: Python, mut iter: &pyo3::types::PyIterator) -> PyResult<Self> {
        let mut sk = hyperminhash::Sketch::default();
        loop {
            // SAFETY: We never observe `obj` after hashing it
            let pool = unsafe { py.new_pool() };
            match iter.next() {
                Some(obj) => {
                    obj?.extract().map(|h| sk.add_bytes(h))?;
                }
                None => {
                    break;
                }
            }
            drop(pool);
        }
        Ok(Self { inner: sk })
    }

    /// Serialize this Sketch into an opaque buffer.
    fn save(&self) -> PyResult<std::borrow::Cow<[u8]>> {
        let mut buf = Vec::with_capacity(32768);
        self.inner.save(&mut buf)?;
        Ok(std::borrow::Cow::from(buf))
    }

    /// Add any object to this Sketch using the object's `hash()`
    fn add(&mut self, obj: &PyAny) -> PyResult<()> {
        obj.hash().map(|h| self.inner.add(h))
    }

    /// Add a bytes-object to this Sketch
    fn add_bytes(&mut self, buf: &[u8]) {
        self.inner.add_bytes(buf);
    }

    /// The estimated number of unique objects in this Sketch
    fn cardinality(&self) -> f64 {
        self.inner.cardinality()
    }

    /// Merge another Sketch into this instance
    fn union(&mut self, other: &Self) {
        self.inner.union(&other.inner);
    }

    /// Compute the estimated number of unique objects that are present in both Sketches
    fn intersection(&self, other: &Self) -> f64 {
        self.inner.intersection(&other.inner)
    }

    /// Return `False` if this Sketch is empty
    fn __bool__(&self) -> bool {
        self.cardinality() != 0.0
    }

    /// Same as `.cardinality()`, rounded to an `int`
    fn __int__(&self) -> u64 {
        self.cardinality().round() as u64
    }

    /// Same as `.cardinality()`, rounded to an `int`
    fn __len__(&self) -> PyResult<usize> {
        Ok(usize::try_from(self.__int__())?)
    }

    /// Same as `.cardinality()`
    fn __float__(&self) -> f64 {
        self.cardinality()
    }

    /// Same as `.union`
    fn __iand__(&mut self, other: &Self) {
        self.union(other)
    }

    /// Same as `.union`, but creating a new Sketch in the process
    fn __and__(&self, other: &Self) -> PyResult<Self> {
        let mut inner = self.inner.clone();
        inner.union(&other.inner);
        Ok(Self { inner })
    }
}

#[pyfunction]
fn __version_info__() -> PyResult<String> {
    Ok(format!(
        "built by `{}` using `{}`",
        built_info::RUSTC_VERSION,
        built_info::DIRECT_DEPENDENCIES_STR
    ))
}

/// A Python module implemented in Rust.
#[pymodule]
fn pyhyperminhash(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Sketch>()?;
    m.add_function(wrap_pyfunction!(__version_info__, m)?)?;
    m.add("__version__", built_info::PKG_VERSION)?;
    m.add("__profile__", built_info::PROFILE)?;
    Ok(())
}
