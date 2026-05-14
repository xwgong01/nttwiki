---
hide:
  - footer
---

# Code guidelines

Two general places to find information on C++-specific questions are [cppreference](https://en.cppreference.com/w/) and [learncpp](https://www.learncpp.com/). For Kokkos-related questions, one can refer to the [Kokkos documentation](https://kokkos.org/kokkos-core-wiki/) as well as the [Kokkos tutorials](https://github.com/kokkos/kokkos-tutorials) for practical examples. For ADIOS2-related issues, refer to the [ADIOS2 documentation](https://adios2.readthedocs.io/en/latest/), and the [examples on their github](https://github.com/ornladios/ADIOS2/tree/master/examples).

When not sure what a specific function does, or how to include a particular module, first check [the documentation](https://entity-toolkit.github.io/wiki) (you can do a keyword search). Another good option to figure things out on your own, is to look at how the particular modules/functions in questions are used in the unit tests (in the corresponding `tests/` directories). If non of that answers your questions, please feel free to open a [github issue](https://github.com/entity-toolkit/entity/issues).

!!! note "Submitting a github issue"

    When submitting a github issue, please make sure to include all the parameters of the simulation as well as the code version tag and the git hash of the commit you are using. These are automatically printed into `stdout` at the beginning of the simulation, and are also saved into `<simname>.info` file. If you believe the problem is coming from your problem generator, please also include the problem generator file. 

--8<-- "docs/assets/imported/code-guidelines.md"
