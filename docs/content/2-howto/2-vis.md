---
hide:
  - footer
---

# Output & visualization

To enable the runtime output of the simulation data, configure the code with the `-D output=ON` flag. As a backend `Entity` uses the open-source [ADIOS2](https://github.com/ornladios/ADIOS2) library compiled in-place. The output is written in the `ADIOS2` format called `BP5`, but [HDF5](https://adios2.readthedocs.io/en/latest/engines/engines.html#hdf5) is also available (but not recommended). 

The output is configured using the following configurations in the `input` file:

```toml
[simulation]
  name   = "MySimulation" # (5)!

  # ...
[[particles.species]]
  tracking = true # (15)!

  # ...
[output]
  format = "BPFile" # (2)!
  interval = 100 # (3)!
  interval_time = 0.1 # (8)!

  [output.fields]
    quantities = ["B", "E", "Rho_1_2", "..."] # (1)!
    stride = 2 # (9)!
    mom_smooth = 2 # (4)!

  [output.particles]
    species = [1, 2, 4] # (7)!
    stride = 10 # (6)!

  [output.spectra]
    e_min = 1e-2 # (12)!
    e_max = 1e3
    log_bins = true # (13)!

  [output.stats]
    quantities = ["N", "Npart", "ExB", "J.E"] # (14)!

  [output.debug]
    as_is = false # (10)!
    ghosts = false # (11)!
```

1. fields to write
2. output format (current supported: "BPFile"/"HDF5", or "disabled" for no output)
3. output interval (in the number of time steps)
4. smoothing stencil size for moments (in the number of cells) [defaults to 1]
5. title is used for the output filename
6. stride used for particle output (write every `prtl_stride`-th particle) [defaults to 100]
7. particle species to output
8. output interval in time units (overrides `interval` if specified)
9. stride used for field output (write every `fields_stride`-th cell) [defaults to 1]
10. write the field quantities as-is (without conversion/interpolation) [defaults to false]
11. write the ghost cells [defaults to false]
12. Min/max energies for binning the energy distribution [default to 1e-3 -> 1e3]
13. whether to use logarithmic energy bins or linear
14. box reduced quantities to output as stats
15. enable tracking for a given particle species

For the full list, please look at the `input.example.toml` file or refer to the [following section](../1-getting-started/3-inputfile.md).

Following is the list of all supported fields

| Field name | Description                              | Normalization  |
| ---------- | ---------------------------------------- | -------------- |
| `E`        | Electric field (all components)          | $B_0$          |
| `B`        | Magnetic field (all components)          | $B_0$          |
| `D`        | GR: electric field (all components)      | $B_0$          |
| `H`        | GR: aux. magnetic field (all components) | $B_0$          |
| `J`        | Current density (all components)         | $4\pi q_0 n_0$ |
| `Rho`      | Mass density                             | $m_0 n_0$      |
| `Charge`   | Charge density                           | $q_0 n_0$      |
| `N`        | Number density                           | $n_0$          |
| `V`        &nbsp;<a href="https://github.com/entity-toolkit/entity/pull/69"> <span class="since-version">1.2.0</span> </a> | Mean 3-velocity                          | dimensionless |
| `Nppc`     | Raw number of particles per cell         | dimensionless  |
| `Tij`      | Energy-momentum tensor (all components)  | $m_0 n_0$      |
| `divE`    &nbsp;<a href="https://github.com/entity-toolkit/entity/pull/69"> <span class="since-version">1.2.0</span> </a> | Divergence of $E$                        | arb. units     |
| `divD`   &nbsp;<a href="https://github.com/entity-toolkit/entity/pull/69"> <span class="since-version">1.2.0</span> </a>  | GR: divergence of $D$                    | arb. units     |
| `A`        | GR: 2D vector potential $A_\varphi$      | arb. units     |

and particle quantities

| Particle quantity | Description                                               | Units         |
| ----------------- | --------------------------------------------------------- | ------------- |
| `X`               | Coordinates (all components)                              | physical      |
| `U`               | Four-velocities (all components)                          | dimensionless |
| `W`               | Weights                                                   | dimensionless |
| `PLDR` &nbsp;<a href="https://github.com/entity-toolkit/entity/pull/144"> <span class="since-version">1.3.0</span> </a>           | Real-valued payloads                                      | arbitrary     |
| `PLDI` &nbsp;<a href="https://github.com/entity-toolkit/entity/pull/144"> <span class="since-version">1.3.0</span> </a>           | Integer-valued payloads                                   | arbitrary     |
| `RNK` &nbsp;<a href="https://github.com/entity-toolkit/entity/pull/144"> <span class="since-version">1.3.0</span> </a>            | Meshblock rank the particle was created (if MPI is ON)    | --            |
| `IDX` &nbsp;<a href="https://github.com/entity-toolkit/entity/pull/144"> <span class="since-version">1.3.0</span> </a>            | Index of the particle on the given rank                   | --            |

<a href="https://github.com/entity-toolkit/entity/pull/69"> <span class="since-version">1.2.0</span> </a> The code also has an output of box-averaged stats into a `.csv` file, which are simply scalars per each output timestep. The following quantities can be computed

| Box-reduced quantity   | Description                                               | Units              |
| ---------------------- | --------------------------------------------------------- | ------------------ |
| `E^2`                  | Mean $E^2$                                                | $B_0^2$            |
| `B^2`                  | Mean $B^2$                                                | $B_0^2$            |
| `ExB`                  | Mean $\bm{E}\times \bm{B}$                                | $B_0^2$            |
| `J.E`                  | Mean $\bm{J}\cdot \bm{E}$                                 | $4\pi q_0 n_0 B_0$ |
| `N`                    | Mean $n$                                                  | $n_0$              |
| `Npart`                | Total # of particles                                      | dimensionless      |
| `Rho`                  | Mean mass density                                         | $m_0 n_0$          |
| `Charge`               | Mean charge density                                       | $q_0 n_0$          |
| `Tij`                  | Mean energy-momentum tensor (all components)              | $m_0 n_0$          |

"Mean" in this context refers to volume-averaging: i.e., $\langle E_x^2 \rangle = V^{-1}\int \sqrt{h} d^3 \bm{x}~ E_x^2 $, or $\langle T^{ij}\rangle \equiv V^{-1} \int d^3\bm{u} \sqrt{h} d^3 \bm{x} ~(u^i u^j / u^0) f(\bm{u}) $, where $V\equiv \int \sqrt{h} d^3\bm{x}$. As such, these values (except for `Npart`) are insensitive to the resolution of the grid or the number of particles per cell.

!!! note "Refining moments for the output"

    One can specify particular components to output for the `Tij` fields/stats: `T0i` will output the `T00`, `T01`, and `T02` components, while `Tii` will output only the diagonal components: `T11`, `T22`, and `T33`, and `Tij` will output all the 6 components. For quantities computed from particles (moments of the distribution), one can also specify the particle species which will be used to compute the moments: `Rho_1` (density of species 1), `N_2_3` (number density of species 2 and 3), `Tij_1_3` (energy-momentum tensor for species 1 and 3), etc. 

All of the vector fields are interpolated to cell centers before the output, and converted to orthonormal basis. The particle-based moments are smoothed with a stencil (specified in the input file; `mom_smooth`) for each particle.

In addition, one can write custom user-defined field quantities to the output with the fields or stats. Refer to [the following section](../2-howto/1-problem_generators.md#custom-field-output) for more details.

!!! success "Can one track particles at different times?"

    <span class="since-version">1.3.0</span> Yes! Simply enable particle tracking for a particular species. Then each particle is uniquely identified by a combination of `IDX` and `RNK` (if no MPI is used, then only `IDX` is sufficient). `nt2py` already automatically combines the variables producing a unique `id` for each particle (for the species where tracking is enabled). However, keep in mind, that the simulations are not reproducible and will unfortunately never be due to limitations imposed by the nature of GPU computations. 

## [`nt2py`](https://pypi.org/project/nt2py/)

We provide the `nt2py` python package to help easily access and manipulate the simulation data. `nt2py` package uses the [`dask`](https://docs.dask.org/en/stable/) and [`xarray`](https://docs.xarray.dev/en/stable/) libraries together with [`adios2`](https://pypi.org/project/adios2/) and/or [`h5py`](https://pypi.org/project/h5py/) to [lazily load](https://en.wikipedia.org/wiki/Lazy_loading) the output data and provide a convenient interface for the data analysis and quick visualization. 

To start using `nt2py`, it is recommended to create a python virtual environment and install the required packages:

```shell
python3 -m venv .venv
source .venv/bin/activate # (1)!
pip install nt2py # (2)!
```

1. Now all the packages will be installed in the `.venv` directory which you can remove at any time without affecting the system.
2. If you plan to use jupyter you might also need to run the following `pip install jupyterlab ipykernel`.

--8<-- "docs/assets/imported/nt2py-readme.md"

