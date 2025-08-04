from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        "cubeCom",
        ["lib.cpp", "Talk.cpp"],
        include_dirs=[pybind11.get_include()],
        define_macros=[("PPPY", None)],
        language="c++",
    ),
]

setup(
    name="cubeCom",
    version="0.0.1",
    ext_modules=ext_modules,
)
