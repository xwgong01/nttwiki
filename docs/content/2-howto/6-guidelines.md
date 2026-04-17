---
hide:
  - footer
---

# Code guidelines

Two general places to find information on C++-specific questions are [cppreference](https://en.cppreference.com/w/) and [learncpp](https://www.learncpp.com/). For Kokkos-related questions, one can refer to the [Kokkos documentation](https://kokkos.org/kokkos-core-wiki/) as well as the [Kokkos tutorials](https://github.com/kokkos/kokkos-tutorials) for practical examples. For ADIOS2-related issues, refer to the [ADIOS2 documentation](https://adios2.readthedocs.io/en/latest/), and the [examples on their github](https://github.com/ornladios/ADIOS2/tree/master/examples).

When not sure what a specific function does, or how to include a particular module, first check [the documentation](https://entity-toolkit.github.io/wiki) (you can do a keyword search). Another good option to figure things out on your own, is to look at how the particular modules/functions in questions are used in the unit tests (in the corresponding `tests/` directories). If non of that answers your questions, please feel free to open a [github issue](https://github.com/entity-toolkit/entity/issues).

!!! note "Submitting a github issue"

    When submitting a github issue, please make sure to include all the parameters of the simulation as well as the code version tag and the git hash of the commit you are using. These are automatically printed into `stdout` at the beginning of the simulation, and are also saved into `<simname>.info` file. If you believe the problem is coming from your problem generator, please also include the problem generator file. 

## Codestyle guide

### `clang-format`

To maintain coherence throughout the source code, we use `clang-format` to enforce a uniform style. A corresponding `.clang-format` file with all the style-related settings can be found in the root directory of the code. To use this, one needs to have the `clang-format` executable (typically provided with the `llvm` package). After installing the `clang-format` itself (check by running `clang-format --version`), you can use it either manually by running `clang-format .` in the route directory of the code, or attach it to your favorite code editor to run on save. For VSCode, the recommended extension is [`xaver.clang-format`](https://github.com/xaverh/vscode-clang-format), for vim -- [`rhysd/vim-clang-format`](https://vimawesome.com/plugin/vim-clang-format), for nvim -- [`stevearc/conform.nvim`](https://github.com/stevearc/conform.nvim), for [emacs](https://www.vim.org/download.php).


### General

* Use `const` and `auto` declarations where possible.
  
* For real-valued literals, use `ONE`, `ZERO`, `HALF` etc. instead of `1.0`, `0.0`, `0.5` to ensure the compiler will not need to cast. If the value is not defined as a macro, use `static_cast<real_t>(123.4)`.
  
* In problem generators, it is usually a good practice to enumerate all the code configurations the code works with. For instance, if your code only works with 3D Minkowski metric in SRPIC, include the following in your `PGen` class:
  ```cpp
  template <SimEngine::type S, class M>
  struct PGen : public ProblemGenerator<S, M> {
    static constexpr auto engines {
      arch::traits::pgen::compatible_with<SimEngine::SRPIC>::value
    };
    static constexpr auto metrics {
      arch::traits::pgen::compatible_with<Metric::Minkowski>::value
    };
    static constexpr auto dimensions {
      arch::traits::pgen::compatible_with<Dim::_3D>::value
    };
    // ...
  };
  ```
  This will allow the code to throw a compile-time error if the problem generator is used with an incompatible configuration.

### Developers

* Use `{}` in declarations to signify a null (placeholder) value for the given variable:
  ```cpp
  auto a { -1 }; // <- value of `a` will be changed later (-1 is a placeholder)
  auto b = -1; // <- value of `b` is known at the time of declaration (but may change later)
  const auto b = -1; // <- value of `b` is not expected to change later
  ```
* Each header file has to have a description at the top, consisting of the following fields:
    * `@file` **[required]** the name of the file (as it should be included in other files)
    * `@brief` **[required]** brief description of what the file contains
    * `@implements` list of class/function/macros implementations
        - structs/classes in this section have no prefix (templates are marked with `<>`)
        - functions are marked with their return type, e.g. ` -> void`
        - type aliases have a prefix `type`
        - enums or enum-like objects are marked with `enum`
        - macros have a prefix `macro`
        - all of the above are also marked with their respective namespaces (if any): `namespace::`
    * `@cpp:` list of cpp files that implement the header
    * `@namespaces:` list of namespaces defined in the file
    * `@macros:` list of macros that the file depends on
    * `@note` any additional notes (stack as many as necessary)

    !!! code "Example"

        ```c++
        /**
          * @file output/particles.h
          * @brief Defines the metadata for particle output
          * @implements
          *   - out::OutputParticle
          * @cpp:
          *   - particles.cpp
          */
        ```

* `#ifdef` macros should be avoided. Use C++17 type traits or `if constexpr ()` expressions to specialize functions and classes instead (ideally, specialize them explicitly). `#ifdef`-s are only acceptable in platform/library-specific parts of the code (e.g., `MPI_ENABLED`, `GPU_ENABLED`, `DEBUG`, etc.).

* Header files should start with `#ifndef ... #define ...` and end with `#endif`; do not use `#pragma` guards. The name of the macro should be the same as the name of the file in uppercase, with underscores instead of dots and slashes. For example, for `global/utils/formatting.h`, the macro should be `GLOBAL_UTILS_FORMATTING_H`.

* There is no difference between `.h` and `.hpp` files as both indicate C++ header files. As a consistency convention, we use `.h` for common headers which may be included from multiple `.cpp` files (e.g., metrics), while `.hpp` are very specific headers for only a single (or a couple of) `.cpp` file (e.g. kernels).

### Recommendations

* Do assertions on parameters and quantities whenever possible. Outside the kernels, use `raise::Error(message, HERE)` and `raise::ErrorIf(condition, message, HERE)` to throw exceptions. Inside the kernels, use `raise::KernelError(HERE, message, **args)`. To enable compile-time errors, use `static_assert(condition, message)`. The `HERE` keyword is macro that includes the filename and line number in the error message.

* When writing class or function templates, it is always a good practice to ensure the template argument is valid (depending on the context). When doing that, use SFINAE (see, e.g., `arch/traits.h`) to test whether the type is valid. For example:
  ```cpp
  template <typename T>
  using foo_t = decltype(&T::foo);

  template <typename T>
  using b_t = decltype(&T::b);

  template <class B>
  class A {
    // compile-time fail if B does not have a `foo()` method or a `b` member
    static_assert(traits::has_method<foo_t, B>::value, "B must have a `foo()` method");
    static_assert(traits::has_member<b_t, B>::value, "B must have a `b` member");
  };
  ```
