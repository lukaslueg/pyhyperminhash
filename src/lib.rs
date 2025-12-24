use pyo3::prelude::*;

pub mod built_info {
    include!(concat!(env!("OUT_DIR"), "/built.rs"));
}

struct PyFileLikeObject(Py<PyAny>);

impl std::io::Read for PyFileLikeObject {
    fn read(&mut self, buf: &mut [u8]) -> Result<usize, std::io::Error> {
        Python::attach(|py| {
            let bytes = self
                .0
                .bind(py)
                .call_method1(pyo3::intern!(py, "read"), (buf.len(),))?;
            let bytes = bytes.extract::<std::borrow::Cow<[u8]>>().map_err(|err| {
                std::io::Error::new(std::io::ErrorKind::InvalidInput, err.to_string())
            })?;
            buf[..bytes.len()].copy_from_slice(&bytes);
            Ok(bytes.len())
        })
    }
}

// TODO The Box<> is a temporary fix for pyo3 #5714
#[pyclass(eq)]
#[derive(Clone, PartialEq)]
struct Entry {
    inner: Box<hyperminhash::Entry>,
}

/// A temporary object that represents a single (possibly unique) object in a `Sketch`, comprised
/// of multiple parts.
///
/// ```python
/// sk = pyhyperminhash.Sketch()
///
/// e = pyhyperminhash.Entry()
/// e.add('User1')  # `e` now represents `('User1', )`
///
/// e_page1 = e.fork()
/// e_page1.add('Page1')  # ... `('User1', 'Page1')`
/// sk.add_entry(e_page1)
///
/// e.add('Page2')  # ... `('User1', 'Page2')`
/// sk.add_entry(e)
///
/// # `sk` now contains two unique objects
/// ```
#[pymethods]
impl Entry {
    #[classattr]
    const __hash__: Option<Py<PyAny>> = None;

    #[new]
    fn new() -> Self {
        Self {
            inner: Box::default(),
        }
    }

    /// Add any object to this `Entry` using the object's `hash()`.
    #[pyo3(signature=(obj, /))]
    fn add(&mut self, py: Python<'_>, obj: &Bound<'_, PyAny>) -> PyResult<()> {
        if let Ok(b) = obj.extract::<std::borrow::Cow<[u8]>>() {
            py.detach(|| self.inner.add(b));
        } else {
            let h = obj.hash()?;
            py.detach(|| self.inner.add(h));
        }
        Ok(())
    }

    fn __iadd__(&mut self, py: Python<'_>, obj: &Bound<'_, PyAny>) -> PyResult<()> {
        self.add(py, obj)
    }

    /// Read a file-like object and add it to this Entry
    #[pyo3(signature=(src, /))]
    fn add_reader(&mut self, py: Python<'_>, src: Py<PyAny>) -> PyResult<u64> {
        Ok(py.detach(|| self.inner.add_reader(PyFileLikeObject(src)))?)
    }

    /// Creates an independent copy of this Entry in its current state
    fn fork(&self) -> Self {
        self.clone()
    }
}

/// Very fast, constant memory-footprint cardinality approximation, including intersection and union operation.
#[pyclass(eq, ord)]
#[derive(PartialEq, PartialOrd)]
struct Sketch {
    inner: hyperminhash::Sketch,
}

#[pymethods]
impl Sketch {
    #[classattr]
    const __hash__: Option<Py<PyAny>> = None;

    #[new]
    fn new() -> Self {
        Self {
            inner: hyperminhash::Sketch::default(),
        }
    }

    /// Deserialize an instance from a buffer given by `Sketch.save()`
    #[staticmethod]
    #[pyo3(signature=(buf, /))]
    fn load(buf: &[u8]) -> PyResult<Self> {
        Ok(Self {
            inner: hyperminhash::Sketch::load(buf)?,
        })
    }

    /// Construct a new Sketch from an iterator of objects
    #[staticmethod]
    #[pyo3(signature=(src, /))]
    fn from_iter(src: Bound<'_, pyo3::types::PyIterator>) -> PyResult<Self> {
        let inner = src
            .map(|maybe_obj| maybe_obj.and_then(|obj| obj.hash()))
            .collect::<PyResult<hyperminhash::Sketch>>()?;
        Ok(Self { inner })
    }

    /// Serialize this Sketch into an opaque buffer.
    fn save(&mut self) -> PyResult<std::borrow::Cow<'_, [u8]>> {
        let mut buf = Vec::with_capacity(32768);
        self.inner.save(&mut buf)?;
        Ok(std::borrow::Cow::from(buf))
    }

    /// Add any object to this Sketch using the object's `hash()`
    #[pyo3(signature=(obj, /))]
    fn add(&mut self, py: Python<'_>, obj: &Bound<'_, PyAny>) -> PyResult<()> {
        let mut e = Entry::new();
        e.add(py, obj)?;
        self.add_entry(&e);
        Ok(())
    }

    fn __iadd__(&mut self, py: Python<'_>, obj: &Bound<'_, PyAny>) -> PyResult<()> {
        self.add(py, obj)
    }

    /// Read a file-like object and add it to this Sketch
    #[pyo3(signature=(src, /))]
    fn add_reader(&mut self, py: Python<'_>, src: Py<PyAny>) -> PyResult<u64> {
        let mut e = Entry::new();
        let r = e.add_reader(py, src)?;
        self.add_entry(&e);
        Ok(r)
    }

    #[pyo3(signature=(entry, /))]
    fn add_entry(&mut self, entry: &Entry) {
        self.inner.add_entry(&entry.inner);
    }

    /// The estimated number of unique objects in this Sketch
    fn cardinality(&self, py: Python<'_>) -> f64 {
        py.detach(|| self.inner.cardinality())
    }

    /// Merge another Sketch into this instance
    #[pyo3(signature=(other, /))]
    fn union(&mut self, py: Python<'_>, other: &Self) {
        py.detach(|| self.inner.union(&other.inner));
    }

    /// Compute the estimated number of unique objects that are present in both Sketches
    #[pyo3(signature=(other, /))]
    fn intersection(&mut self, py: Python<'_>, other: &Self) -> f64 {
        py.detach(|| self.inner.intersection(&other.inner))
    }

    /// The Jaccard Index similarity estimation
    #[pyo3(signature=(other, /))]
    fn similarity(&self, py: Python<'_>, other: &Self) -> f64 {
        py.detach(|| self.inner.similarity(&other.inner))
    }

    /// Return `False` if this Sketch is empty
    fn __bool__(&self, py: Python<'_>) -> bool {
        self.cardinality(py) != 0.0
    }

    /// Same as `.cardinality()`, rounded to an `int`
    fn __int__(&self, py: Python<'_>) -> u64 {
        self.cardinality(py).round() as u64
    }

    /// Same as `.cardinality()`, rounded to an `int`
    fn __len__(&self, py: Python<'_>) -> PyResult<usize> {
        Ok(usize::try_from(self.__int__(py))?)
    }

    /// Same as `.cardinality()`
    fn __float__(&self, py: Python<'_>) -> f64 {
        self.cardinality(py)
    }

    /// Same as `.union`
    fn __iand__(&mut self, py: Python<'_>, other: &Self) {
        self.union(py, other);
    }

    /// Same as `.union`, but creating a new Sketch in the process
    fn __and__(&self, py: Python<'_>, other: &Self) -> Self {
        py.detach(|| {
            let mut inner = self.inner.clone();
            inner.union(&other.inner);
            Self { inner }
        })
    }
}

#[pyfunction]
fn __version_info__() -> String {
    format!(
        "built by `{}` using `{}`",
        built_info::RUSTC_VERSION,
        built_info::DIRECT_DEPENDENCIES_STR
    )
}

#[allow(clippy::single_match)]
const fn __hyperminhash_version__() -> &'static str {
    let mut idx = 0;
    while idx < built_info::DEPENDENCIES.len() {
        let (pkg, version) = built_info::DEPENDENCIES[idx];
        match pkg.as_bytes() {
            b"hyperminhash" => {
                return version;
            }
            _ => {}
        }
        idx += 1;
    }
    ""
}

/// Hyperminhash bindings for `CPython`
#[pymodule]
#[allow(non_upper_case_globals)]
mod pyhyperminhash {
    #[pymodule_export]
    const __version__: &str = super::built_info::PKG_VERSION;

    #[pymodule_export]
    const __profile__: &str = super::built_info::PROFILE;

    #[pymodule_export]
    const __hyperminhash_version__: &str = super::__hyperminhash_version__();

    #[pymodule_export]
    use super::__version_info__;

    #[pymodule_export]
    use super::Entry;

    #[pymodule_export]
    use super::Sketch;
}
