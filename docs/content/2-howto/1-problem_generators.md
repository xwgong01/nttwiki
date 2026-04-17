---
hide:
  - footer
libraries:
  - d3
scripts:
  - atm-boundaries
---

# Customizing your setup

!!! abstract "Relevant headers"

    - `setups/**/pgen.hpp`
    - `archetypes/problem_generator.h`
    - `archetypes/field_setter.h`
    - `archetypes/energy_dist.h`
    - `archetypes/spatial_dist.h`
    - `archetypes/particle_injector.h`

## Problem generators

Problem generators describe a specific simulation setup (e.g., initial conditions) for the `Entity` engines to use to run the simulation. All problem generators are stored in the `pgens` directory each in a separate parent directory and are all named `pgen.hpp`. It is a good practice to also store a sample `*.toml` input file and a `*.py` visualization file corresponding to that problem generator. Problem generators are chosen at compile time using the `-D pgen=...` flag, where `...` is the relative path where the problem generator is stored. For instance, to pick the `pgens/streaming/pgen.hpp` problem generator, one would use the following command:

```bash
cmake ... -D pgen=streaming
```

### Basic structure

All problem generators contain a namespace `user::` and a structure named `Pgen<S, M>` which must inherit from the `arch::ProblemGenerator<S, M>` class, where `S` is the simulation engine and `M` is the metric. A typical dummy problem generator will look like this:

```cpp
#ifndef PROBLEM_GENERATOR_H
#define PROBLEM_GENERATOR_H

#include "enums.h"
#include "global.h"

#include "archetypes/traits.h"
#include "archetypes/problem_generator.h"
#include "framework/domain/metadomain.h"
#include "framework/parameters/parameters.h"

namespace user {
  using namespace ntt; // (2)!

  template <SimEngine::type S, class M>
  struct PGen : public arch::ProblemGenerator<S, M> {
    // enumerate which engines/metrics/dimensions are compatible (1)
    static constexpr auto engines {
      arch::traits::pgen::compatible_with<SimEngine::SRPIC, SimEngine::GRPIC>::value
    };
    static constexpr auto metrics {
      arch::traits::pgen::compatible_with<Metric::Minkowski,
                              Metric::Spherical,
                              Metric::QSpherical,
                              Metric::Kerr_Schild,
                              Metric::QKerr_Schild,
                              Metric::Kerr_Schild_0>::value
    };
    static constexpr auto dimensions {
      arch::traits::pgen::compatible_with<Dim::_1D, Dim::_2D, Dim::_3D>::value
    };

    // ... additional definitions ..

    inline PGen(const SimulationParams& p, const Metadomain<S, M>&)
      : arch::ProblemGenerator<S, M> { p } 
      // ... any additional initialization ...
      {}

    // ... additional methods ...
  };

} // namespace user

#endif // PROBLEM_GENERATOR_H
```

1. This is done not only for the runtime sanity check, but also to shorten the compile time, as the compiler will not generate the code for the incompatible engines/metrics/dimensions.
2. To avoid using `ntt::` everywhere

There are three special definitions one may provide in the problem generator that will allow the simulation engine to call custom routines at the beginning of the simulation or at the end of each timestep.

!!! note "Units"

    In all of the functions and classes described below, it is assumed that the end-user designing the problem generator has no knowledge of the inner workings of the code units. All the quantities provided by the user are thus in the natural physical units (i.e., global physical coordinates for the positions and local tetrad basis for the vectors). All the conversions, staggering etc. is done automatically under the hood.

### Initializing fields

To initialize electromagnetic fields to specific values, one may provide a custom class called `init_flds`:

```cpp
template <SimEngine::type S, class M>
struct PGen : public arch::ProblemGenerator<S, M> {
  // ...
  
  // the name of the class may be arbitrary, but the instance must be named `init_flds`
  FancyFieldInitializer init_flds;
};
```

This class (or class template) in turn may have an arbitrarily complex constructor, but it must have any number of the methods `ex1()`, `ex2()`, ... `dx1()`, `dx2()`, etc., which set the corresponding field components. For instance, to set the electric field in the $x_2$ direction to a constant value, one would write:
```cpp
template <Dimension D>
struct NotSoFancyFieldInitializer {
  NotSoFancyFieldInitializer(real_t myval)
    : myvalue { myval } {}

  Inline auto ex2(const coord_t<D>&) const -> real_t {
    return myvalue;
  }
  // you may skip other field components if you don't need them

private:
  const real_t myvalue;
};
```

Notice, that `ex2` takes a single argument of type `coord_t<D>` (coordinate vector), which in this case is empty, since we are not using it. In general, one may define fields as functions of the coordinate. 

```cpp
template <Dimension D>
struct SinusoidalField {
  SinusoidalField(real_t kx, real_t ampl)
    : kx { kx }, amplitude { ampl } {}

  Inline auto bx1(const coord_t<D>& x_Ph) const -> real_t {
    return amplitude * math::sin(kx * x_Ph[1]); // function of x2 coordinate
  }
  // you may skip other field components if you don't need them

private:
  const real_t kx, amplitude;
};

// and then use it in the problem generator
template <SimEngine::type S, class M>
struct PGen : public arch::ProblemGenerator<S, M> {
  // ...
  
  SinusoidalField<D> init_flds;

  // initialize the `init_flds` by passing the parameters from the input
  inline PGen(const SimulationParams& p, const Metadomain<S, M>&)
      : arch::ProblemGenerator<S, M> { p }
      , init_flds { p.template get<real_t>("setup.kx"), 
                    p.template get<real_t>("setup.amplitude") } 
      {}
};
```

Fields must be returned in the local tetrad (orthonormal) basis in SR and coordinate-basis in GR, while the passed coordinates are the global physical coordinates. Conversion to code units and staggering of each corresponding field component is done automatically under the hood.

### Initializing particles

Similar to initializing the fields, one can also initialize particles with a given energy or spatial distribution. This is done by providing a custom method of the `PGen` class called `InitPrtls(Domain<S, M>&)` which takes a reference to the local subdomain as a parameter. In principle, one can manually initialize the particles in any way they want, but it is recommended to use the built-in routines from the `arch::` (archetypes) namespace.

For instance, to initialize a uniform Maxwellian of a given temperature, one can use the `arch::Maxwellian` class together with the `InjectUniform` method:

```cpp
// don't forget to include the proper headers
#include "archetypes/energy_dist.h"
#include "archetypes/particle_injector.h"

// ...

template <SimEngine::type S, class M>
struct PGen : public arch::ProblemGenerator<S, M> {
  // 
  inline void InitPrtls(Domain<S, M>& local_domain) {
    const auto energy_dist = arch::Maxwellian<S, M>(
                                  local_domain.mesh.metric, 
                                  local_domain.random_pool(), 
                                  temperature);
    arch::InjectUniform<S, M, decltype(energy_dist), decltype(energy_dist)>(
                          params,
                          local_domain,
                          { 1, 2 },
    //                      ^^^^^
    //                      species to inject    
                          { energy_dist, energy_dist },
    //                      ^^^^^        ^^^^^
    //                      energy distributions for each species
                          1.0); // <-- this is the number density in units of `n0`
  }
};
```

To initialize a non-uniform distribution and/or an arbitrary energy distribution, we will need to provide our own classes, which in turn must inherit from the `arch::SpatialDistribution<S, M>` and `arch::EnergyDistribution<S, M>`. For instance, let us initialize a distribution of two particle species counter-streaming in opposing direction with their velocities depending on the $x_2$ ($y$) coordinate, distributed in space according to a Gaussian profile. We first need to define the energy distribution:

```cpp
template <SimEngine::type S, class M>
struct CounterstreamEnergyDist : public arch::EnergyDistribution<S, M> {
  CounterstreamEnergyDist(const M& metric, real_t v_max, real_t sx2)
    : arch::EnergyDistribution<S, M> { metric }
    , v_max { v_max }
    , kx2 { static_cast<real_t>(constant::TWO_PI) / sx2 } {}

  // three arguments passed here are
  // x_Ph: global physical coordinates of the particle
  // v: the velocity of the particle to-be-set in the tetrad basis
  // sp: species index
  Inline void operator()(const coord_t<M::Dim>& x_Ph,
                         vec_t<Dim::_3D>&       v,
                         unsigned short         sp) const {
    if (sp == 1) {
      v[0] = v_max * math::sin(kx2 * x_Ph[1]);
    } else {
      v[0] = -v_max * math::sin(kx2 * x_Ph[1]);
    }
  }

private:
  const real_t v_max, kx2;
};
```

We then need to define the spatial distribution, which takes a coordinate as an argument and returns the probability of a particle to be injected at that point. In our case, we will use a Gaussian profile:

```cpp
template <SimEngine::type S, class M>
struct GaussianDist : public arch::SpatialDistribution<S, M> {
  GaussianDist(const M& metric, real_t x1c, real_t x2c, real_t dr)
    : arch::SpatialDistribution<S, M> { metric }
    , x1c { x1c }
    , x2c { x2c }
    , dr { dr } {}

  // to properly scale the number density, the probability should be normalized to 1
  Inline auto operator()(const coord_t<M::Dim>& x_Ph) const -> real_t {
    return math::exp(-(SQR(x_Ph[0] - x1c) + SQR(x_Ph[1] - x2c)) / SQR(dr));
  }

private:
  const real_t x1c, x2c, dr;
};
```

We can then pass the instances of these classes to the `arch::InjectNonUniform` method called from within the `InitPrtls` method of the problem generator:

```cpp
// definition of CounterstreamEnergyDist and GaussianDist classes
// ...

template <SimEngine::type S, class M>
struct PGen : public arch::ProblemGenerator<S, M> {
  // internal variables to-be-used in the constructor
  const real_t temperature, v_max, sx2;
  const real_t x1c, x2c, dr;

  // read the parameters from the input
  inline PGen(const SimulationParams& p, const Metadomain<S, M>& global_domain)
    : arch::ProblemGenerator<S, M> { p }
    , temperature { p.template get<real_t>("setup.temperature") }
    , v_max { p.template get<real_t>("setup.v_max") }
    , sx2 { global_domain.mesh().extent(in::x2).second - global_domain.mesh().extent(in::x2).first } // (1)!
    , x1c { p.template get<real_t>("setup.x1c") }
    , x2c { p.template get<real_t>("setup.x2c") }
    , dr { p.template get<real_t>("setup.dr") }
    {}

  inline void InitPrtls(Domain<S, M>& local_domain) {
    const auto energy_dist  = CounterstreamEnergyDist<S, M>(
                                        local_domain.mesh.metric,
                                        v_max,
                                        sx2);
    const auto spatial_dist = GaussianDist<S, M>(domain.mesh.metric,
                                                 x1c,
                                                 x2c,
                                                 dr);

    arch::InjectNonUniform<S, M, decltype(energy_dist), decltype(energy_dist), decltype(spatial_dist)>(
            params,
            domain,
            { 1, 2 },
            { energy_dist, energy_dist },
            spatial_dist,
            1.0); // <-- injected density in units of `n0` 
            // (2)!
  }

};
```

1. `x_2` extent of the global domain can be directly read from the metadomain instance passed to the constructor.
2. Here, the value of `1.0` corresponds to the probability of `1.0` returned by the spatial distribution class.

### Custom post-timestep routines

Often times, one needs to intervene to the simulation process to perform some custom operations by updating the fields or the particles (for instance, to apply special boundary conditions, inject particles etc.). The safest way of performing this is at the end of each timestep, when all the quantities have already been computed and stored. For that, Entity allows users to define another special method in the problem generator called `CustomPostStep`. It accepts the current timestep, the current physical time, and the local subdomain as a parameter. For instance, to inject particles at a given rate, one can write:

```cpp
template <SimEngine::type S, class M>
struct PGen : public arch::ProblemGenerator<S, M> {
  // ... 

  void CustomPostStep(std::size_t, long double, Domain<S, M>& domain) {
    // ... some energy/spatial distribution & injector here (see above) ...
    arch::InjectNonUniform<S, M, /* ... */>( /* ... */ );
  }
};
```

Or you may also manually access the fields and particles through the `domain.fields` and `domain.species[...]` objects, respectively, and perform any operations you need. Be mindful, however, that all the raw quantities stored within the `domain` object are in the code units (for more details, see the [fields and particles](../3-code/4-fields_particles.md) section; for ways to convert from one system/basis to another, see the [metric](../3-code/5-metrics.md) section).

### Custom external force

Similar to all the other custom routines, one may also define a custom external force which will optionally be applied to the particles together with the electromagnetic pusher. This is done by defining an arbitrary class with an instance named `ext_force`, which implements three methods: `fx1()`, `fx2()`, `fx3()`. For instance, to apply a force in the $x_1$ direction decaying over time, one would write:

```cpp
template <Dimension D>
struct PushDaTempo {
  // specify which species to apply the force to
  const std::vector<unsigned short> species { 1, 2 };

  PushDaTempo(real_t f, real_t t) : force { f }, tau { t } {}

  Inline auto fx1(const unsigned short&,
                  const real_t& time,
                  const coord_t<D>&) const -> real_t {
    return force * math::exp(-time / tau);
  }

  Inline auto fx2(const unsigned short&,
                  const real_t&,
                  const coord_t<D>&) const -> real_t {
    return ZERO;
  }

  Inline auto fx3(const unsigned short&,
                  const real_t&,
                  const coord_t<D>&) const -> real_t {
    return ZERO;
  }
private:
  const real_t force, tau;
};

// and then in the problem generator class
template <SimEngine::type S, class M>
struct PGen : public arch::ProblemGenerator<S, M> {
  // ...
  PushDaTempo<S, M> ext_force;
  // and read the parameters from the input
  inline PGen(const SimulationParams& p, const Metadomain<S, M>& global_domain)
    : arch::ProblemGenerator<S, M> { p }
    , ext_force { p.template get<real_t>("setup.force"),
                  p.template get<real_t>("setup.tau") }
    {}
};
```

Again, as everything else in the problem generator, the force (rather, the acceleration) must be returned in the local tetrad basis and the passed coordinates are the physical coordinates.


!!! note "All functions are optional"

    Note, that among the functions mentioned throughout this section, you may specify only the ones you actually need, and ignore the ones you don't (i.e., there is no need to provide dummy functions that return zero), as the code will automatically determine at compile-time which functions are present.

### Custom external current

<a href="https://github.com/entity-toolkit/entity/pull/92">
  <span class="since-version">1.2.0</span>
</a>

There are specific instances, where one needs to apply a source term to the Ampere's law as additional (external) currents (e.g., driven turbulence). This can easily be achieved by defining an arbitrary class instance called `ext_current`, which implements 3 methods: `jx1()`, `jx2()`, `jx3()` -- each returning the corresponding external current component in units of $j_0$. For instance, to apply a constant sinusoidal current $j_3$ as a function of $x_1$, one could write:

```cpp
template <Dimension D>
struct ImmaRealLiveWire { //(1)!
  ImmaRealLiveWire(real_t amplitude, real_t k)
    : amp { amplitude }
    , k { k } {};

  Inline auto jx1(const coord_t<D>& x_Ph) const -> real_t {
      return ZERO;
    }

  Inline auto jx2(const coord_t<D>& x_Ph) const -> real_t {
      return ZERO;
    }

  Inline auto jx3(const coord_t<D>& x_Ph) const -> real_t {
      return amp * math::sin(k * x_Ph[0]);
    }

  private:
    const real_t amp, k; 
};

template <SimEngine::type S, class M>
struct PGen : public arch::ProblemGenerator<S, M> {
  ImmaRealLiveWire<D> ext_current;

  inline PGen(const SimulationParams& p, const Metadomain<S, M>& global_domain)
    : arch::ProblemGenerator<S, M> { p }
    , ext_current { p.template get<real_t>("setup.amplitude"),
                    p.template get<real_t>("setup.k") } //(2)!
    {}
};
```  

1. name of the class is not important, as long as its instance declared in the problem generator class itself is called `ext_current`.

2. directly initialize the `ext_current` in the `PGen` constructor by passing values read from the input.

Keep in mind, that in contrast to the external force, all of the components of the current have to be defined in the structure, even if they return zero. 

!!! note "External current"

    The external current routine is currently only limited to work in Minkowski space. 


### Custom field output

The code also allows for custom-defined fields to be written together with other field quantities during the output. To enable that, simply define the name of your field in the input file:

```toml
[output.fields]
  ...
  custom = ["my_field"]
  ...
```

There can be as many custom fields as one needs. And then in the problem generator, populate the corresponding field by defining the following function:

```cpp
void CustomFieldOutput(const std::string&   name,//(1)!
                       ndfield_t<M::Dim, 6> buffer,//(2)!
                       index_t              index,//(3)!
                       timestep_t,//(4)!
                       simtime_t,//(5)!
                       const Domain<S, M>&  domain) {//(6)!
  if (name == "my_field") {
    // 1D example (can be easily generalized)
    if constexpr (M::Dim == Dim::_1D) {
      const auto& EM = domain.fields.em;
      Kokkos::parallel_for(
        "MyField",
        domain.mesh.rangeActiveCells(),
        Lambda(index_t i1) {
          const auto      i1_ = COORD(i1);
          coord_t<M::Dim> x_Ph { ZERO };
          // convert coordinate to physical basis:
          metric.template convert<Crd::Cd, Crd::Ph>({ i1_ }, x_Ph);
          // compute whatever needs to be written
          // ... may also depend on the EM fields from the `domain`
          // ... in this example -- output Ex * x^2
          buffer(i1, index) = SQR(x_Ph[0]) *
                              metric.template transform<1, Idx::U, Idx::T>(
                                { i1_ + HALF },
                                EM(i1, em::ex1));
          // here we also convert Ex1(i + 1/2) to Tetrad basis
        });
    }
  } else {
    raise::Error("Custom output not provided", HERE);
  }
}
```

1. the same name that went into the input file
2. buffer array where the field is going to be written into
3. an index of the buffer array where the field is written into
4. completed step index
5. completed step time in physical units
6. reference of the local subdomain

Alternatively, you can precompute the desired quantity in the `CustomPostStep` function and then simply copy to the buffer in the same function:

```cpp
// assuming 2D and that the desired quantity is saved in `cbuff`
template <SimEngine::type S, class M>
struct PGen : public arch::ProblemGenerator<S, M> {
  // ...

  array_t<real_t**> cbuff;
  
  // ...

  void CustomPostStep(timestep_t step, simtime_t, Domain<S, M>& domain) {
    if (step == 0) {
      // allocate the array at time = 0
      cbuff = array_t<real_t**>("cbuff",
                                domain.mesh.n_all(in::x1),
                                domain.mesh.n_all(in::x2));
    }
    // populate the buffer (can be done at specific timesteps)
    Kokkos::parallel_for(
      "FillCbuff",
      domain.mesh.rangeActiveCells(),
      Lambda(index_t i1, index_t i2) {
        // ...
      });
  }

  void CustomFieldOutput(const std::string&    name,
                         ndfield_t<M::Dim, 6> buffer,
                         index_t              index,
                         timestep_t,
                         simtime_t,
                         const Domain<S, M>&) {
    if (name == "my_field") {
      Kokkos::deep_copy(Kokkos::subview(buffer, Kokkos::ALL, Kokkos::ALL, index), cbuff);
    } else {
      // ...
    }
  }
};
```

Keep in mind that the custom field output is written as-is, i.e., no additional interpolation or transformation is applied. So make sure the quantity you output is covariant (i.e., does not depend on the resolution or the stretching of coordinates; essentially, always output "physical" covariant/contravariant vectors or transform them to the tetrad basis).

### Custom stats

One can also write custom user-defined stats.

```toml
[output.stats]
  ...
  custom = ["my_stat"]
  ...
```

Just like in the case with custom fields, you specify a special function in the problem generator class which has a name `CustomStat` and returns a single real value:

```cpp
auto CustomStat(const std::string&   name,//(1)!
                timestep_t,
                simtime_t,
                const Domain<S, M>&  domain) -> real_t {//(2)!
  if (name == "my_stat") {
    return 42.0;
  } else {
    raise::Error("Custom stat not provided", HERE);
  }
}
``` 

Reduction from all meshblocks of the custom stat is done automatically (the values are summed).

1. the same name that went into the input file
2. reference of the local subdomain

## Boundary Conditions

Entity supports a number of boundary conditions for fields and particles which we will list in the following section.
We currently provide:

```toml
[grid.boundaries]
  # one of: ["PERIODIC", "MATCH", "FIXED", "ATMOSPHERE", "CUSTOM", "HORIZON", "CONDUCTOR"]
  fields = "" 

  # one of: ["PERIODIC", "ABSORB", "ATMOSPHERE", "CUSTOM", "REFLECT", "HORIZON"]
  particles = ""
```

### Periodic boundaries

This boundary condition is valid for both fields and particles and is quite self-explanatory. It simply maps fields and particles outside of the domain on one side into the domain on the other side.

### Atmospheric boundaries

There is a special type of boundary condition named "atmosphere," which applies an additional "gravitational" force to particles and automatically replenishes the plasma to a given target level, while also resetting the fields to a specific value. For Cartesian geometry this boundary condition can be applied in the arbitrary direction, while for spherical/qspherical coordinates, it is only applicable in the $-\hat{x}_1$ (same as $-\hat{r})$ dimension. Thes boundary conditions are specified just like any other ones, via the `fields` and `particles` input parameters of the `[grid.boundaries]` section of the input file. 

The injected particle distribution is in Boltzmann-equilibrium with the gravity: $\bm{u}\cdot\nabla_{\bm{x}} f + m \bm{g}\cdot \nabla_{\bm{u}} f = 0$; the scale-height and the temperature of of the atmosphere are configurable from [the input file](../1-getting-started/3-inputfile.md) using the `grid.boundaries.atmosphere` parameters. The user also has a control over the peak density of the atmosphere, the extent to which the force is acting, as well as the particle species that are being injected. 

```toml
[grid.boundaries.atmosphere]
# @required: if ATMOSPHERE is one of the boundaries
  # Temperature of the atmosphere in units of m0 c^2
  #   @type: float
  temperature = ""
  # Peak number density of the atmosphere at base in units of n0
  #   @type: float
  density = ""
  # Pressure scale-height in physical units
  #   @type: float
  height = ""
  # Species indices of particles that populate the atmosphere
  #   @type: array of ints of size 2
  species = ""
  # Distance from the edge to which the gravity is imposed in physical units
  #   @type: float
  #   @default: 0.0
  #   @note: 0.0 means no limit
  ds = ""
```

While the particle atmospheric boundaries are handled automatically, when field boundaries are set to `ATMOSPHERE`, the user must also provide target electromagnetic fields which will be used to reset the field values below the atmosphere. To do this, one needs to provide a `FieldDriver` method in their problem generator, which takes `time` as an argument and returns an arbitrary class with methods: `ex1`, `ex2`, ... etc. An example of such a class is shown below:

```cpp
template <Dimension D>
struct AtmFields {

  // functions take the physical coordinate as an argument
  Inline auto ex1(const coord_t<D>&) const -> real_t {
    // return something
  }
  
  // ex2, ex3

  Inline auto bx1(const coord_t<D>&) const -> real_t {
    // return something ...
  }

  // bx2, bx3
};

template <SimEngine::type S, class M>
struct PGen : public arch::ProblemGenerator<S, M> {
  // ...

  auto FieldDriver(real_t time) const -> AtmFields<D> {
    return AtmFields<D> { /* ... params ... */ };
  }
};
```

Below is a diagram which indicates how the atmospheric boundary conditions operate (in the example, they are applied in $-\hat{\bm{x}}$ direction). Note, that when the fields are enforced, the normal components of the electric field, and the tangential components of the magnetic field are only enforced below the last (first) cell of the region, whereas the tangential components of the electric field and the normal components of the magnetic field are enforced everywhere (including in the last (first) cell of the region).

<div class="d3-diagram" id="atm-bcs"></div>

### Conductor boundaries

<a href="https://github.com/entity-toolkit/entity/pull/84">
  <span class="since-version">1.2.0</span>
</a>

Another kind of special boundary condition is the perfect (magnetic) conductor boundary. This boundary should be used in combination with reflecting boundaries for particles. You can think of the perfect conductor as introducing a mirror charge outside the boundary.

An example usage can be found in the `srpic/shock/shock.toml`:

```toml
[grid.boundaries]
    fields = [["CONDUCTOR", "MATCH"], ["PERIODIC"]]
    particles = [["REFLECT", "ABSORB"], ["PERIODIC"]]
```

A perfect conductor satisfies the equations $\hat{\boldsymbol{n}} \times \boldsymbol{B} = 0$ and $\hat{\boldsymbol{n}} \cdot \boldsymbol{E} = 0$, where $\hat{\boldsymbol{n}}$ is the surface normal of the boundary. This is achieved by setting $E$- and $B$-field at distance $x$ from the boundary to:

| **E-field** | **B-field** |
| --- | --- | 
| $E_\perp(-\vec{x}) = - E_\perp(+\vec{x})$   | $B_\parallel(-\vec{x}) = - B_\parallel(+\vec{x})$  |
| $E_\perp(0) = 0$                                | $B_\parallel(0) = 0$ |
| $E_\parallel(-\vec{x}) = E_\parallel(+\vec{x})$ | $B_\perp(-\vec{x}) = B_\perp(+\vec{x})$ |

where $\perp$ is the component perpendicular to $\hat{\boldsymbol{n}}$ (tangential to the conductor boundary), while $||$ component is along $\hat{\boldsymbol{n}}$ (perpendicular to the conductor boundary).

Note that the current densities which might propagate beyond the particle stencil due to filtering, should be reflected in the same way as the electric fields; in the `Entity` this is handled at the current filtering kernel. 
<!-- Hence you need at least `current_filters = 1` for this boundary condition to work properly. -->

These boundary conditions do not require any additional input paremeters.

### Match boundaries

<a href="https://github.com/entity-toolkit/entity/pull/69">
  <span class="since-version">1.2.0</span>
</a>

If you want to drive the fields at your boundary to a given value you can do so using the `MATCH` boundary conditions. You can define the width across which the code drives the fields the target values with the `grid.boundaries.match.ds` parameter:

```toml
[grid.boundaries.match]
  # Size of the matching layer in each direction for fields in physical (code) units:
  #   @type: float or array of tuples
  #   @default: 1% of the domain size (in shortest dimension)
  #   @note: In spherical, this is the size of the layer in r from the outer wall
  #   @example: ds = 1.5 (will set the same for all directions)
  #   @example: ds = [[1.5], [2.0, 1.0], [1.1]] (will duplicate 1.5 for +/- x1 and 1.1 for +/- x3)
  #   @example: ds = [[], [1.5], []] (will only set for x2)
  ds = ""
```

!!! note

    Under the hood, the matching boundary conditions simply apply the following condition to the field components:
    $$
      A^{\rm new} = A^{\rm old}s + A^{\rm target} (1-s),~~~ s\equiv \tanh{\left(\frac{|x^i - x^i_b|}{ds_i/4}\right)}
    $$
    where $x^i$ is the physical coordinate in the direction $i$, $x^i_b$ -- is the corresponding boundary in that direction, and $A$ is one of the $E$ (or $D$ in GR) or $B$ components. The user is responsible for supplying the target values (in the problem generator, see below), and the values of $ds_i$ (for all directions) from the input file.

In the problem generator one only needs to define a `MatchFields` method which should inherit from a `struct` that defines the field components you want to drive (the name of the struct can be arbitrary, as long as the name of the function returning it is `MatchFields`). 

```cpp
template <Dimension D>
struct MyBoundaryFields {
  /*
    Defines the fields you want to drive your boundary towards
  */

  // functions take the physical coordinate as an argument
  Inline auto ex1(const coord_t<D>&) const -> real_t {
    // return something
  }
  
  // ex2, ex3

  Inline auto bx1(const coord_t<D>&) const -> real_t {
    // return something ...
  }

  // bx2, bx3
};

template <SimEngine::type S, class M>
struct PGen : public arch::ProblemGenerator<S, M> {
  // ...

  // This function is called within the BC kernel
  // (potentially, bc_flds may depend on time)
  auto MatchFields(simtime_t time) const -> MyBoundaryFields<D> {
    const auto bc_flds = BoundaryFields<D>{};
    return bc_flds;
  }
};
```

All the coordinate conversions and field staggering is performed automatically, so all specified coordinates are in physical units, while the field values are normalized to $B_0$.

If the `struct` does not explicitly define certain components (in the example above, `ex2`, `ex3`, `bx2`, `bx3` are omitted), the code will not apply any specific boundaries to them. If you wish to damp the fields to zero, you will have to explicitly specify it, e.g.,

```cpp
  // ...
  Inline auto ex2(const coord_t<D>&) const -> real_t {
    return ZERO;
  }
```

!!! note "Matching boundaries in different directions"

    You might need to have separate matching boundaries (i.e., fields being matched to different values) in different directions. For example, you may have one set of BCs in $\pm x$, while completely different conditions in $\pm y$. This can be achieved by specifying separately `MatchFieldsInX1` (for $\pm x$) and `MatchFieldsInX2` (in $\pm y$) instead of `MatchFields`. The function will still take time as the argument and return a class defining BCs in each distinct direction.

### Fixed field boundaries

<a href="https://github.com/entity-toolkit/entity/pull/69">
  <span class="since-version">1.2.0</span>
</a>

With `FIXED` boundary conditions you can explicitly set the field components at the boundary cells to a given predefined value. For this you need to define a method `FixFieldsConst(const bc_in&, const em& comp)` which should return a pair of the value you want to set, and a bool if the component should be set or not.

In this example, the $E^2$, and $E^3$ components are set to zero in the boundary, while all the other components remain untouched:

```cpp
// ...

template <SimEngine::type S, class M>
struct PGen : public arch::ProblemGenerator<S, M> {
  // ...

  // This function is called within the BC kernel
  // the first element in the pair ...
  // ... determines the value to which the component is set
  // while the second bool component ...
  // ... determines whether that component is updated at all
  // ... i.e., if bool is false, the first component is simply ignored
  auto FixFieldsConst(const bc_in&, const em& comp) const
      -> std::pair<real_t, bool> {
      if (comp == em::ex2) {
        return { ZERO, true };
      } else if (comp == em::ex3) {
        return { ZERO, true };
      } else {
        return { ZERO, false };
      }
    }
};
```

!!! hint "Changing BCs at runtime"

    One can change the boundary conditions at runtime by directly accessing the global metadomain, for example, in the `CustomPostStep` routine. Below is an example of how to do that (chaging boundaries to `MATCH` for fields and `ABSORB` for particles in $\pm x$ and $\pm y$ at a certain time):
    ```cpp
    template <SimEngine::type S, class M>
    struct PGen : public arch::ProblemGenerator<S, M> {
      // ...
      Metadomain<S, M>& metadomain;
      bool bc_opened { false };
      // ...
      inline PGen(const SimulationParams& p, Metadomain<S, M>& m) : 
        : arch::ProblemGenerator<S, M>(p)
        , metadomain { m } {}

      void CustomPostStep(timestep_t, simtime_t time, Domain<S, M>&) {
        if ((time > t_open) and (not bc_opened)) { // (1)!
          bc_opened = true;
          metadomain.setFldsBC(bc_in::Mx1, FldsBC::MATCH); // (2)!
          metadomain.setPrtlBC(bc_in::Mx1, PrtlBC::ABSORB);
          metadomain.setFldsBC(bc_in::Px1, FldsBC::MATCH);
          metadomain.setPrtlBC(bc_in::Px1, PrtlBC::ABSORB);
        }
        // ...
      }
    };
    ```

    1. check if not already opened & open after certain time
    2. first argument is the direction in which to change the boundary; `M`/`P` stand for minus/plus


## Particle purging

The custom post-timestep can also be used to purge particles within a given region of the domain. This can be useful to inject fresh plasma in the part of the domain and make sure that the old plasma has been removed before replenishing.

!!! warning "Conserving the currents"

    Keep in mind that removing charged particles in general will violate charge conservation, unless the $E$-fields are then explicitly forced to obey $\nabla\cdot\boldsymbol{E}=4\pi \rho$. For that reason, in the example below, along with purging particles we will also reset the fields in that region.

Below we use the example from the shock setup to illustrate particle purging routine. Here, all plasma particles that have $x>x_{\rm min}$ (denoted `xmin` in the code) is purged and the fields are reset before new plasma is injected.

```cpp
template <Dimension D>
struct InitFields {
  /**
   * Defines the fields at initialisation
  **/

  Inline auto ex1(const coord_t<D>&) const -> real_t {
    return /*...*/; //(1)!
  }

  Inline auto bx1(const coord_t<D>&) const -> real_t {
    return /*...*/;
  }
};

template <SimEngine::type S, class M>
struct PGen : public arch::ProblemGenerator<S, M> {
  InitFields<D> init_flds;

  void CustomPostStep(timestep_t step, simtime_t time, Domain<S, M>& domain) {
    /**
     * tag particles inside the injection zone as dead
    **/
    const auto& mesh = domain.mesh;
    // loop over particle species
    for (auto s { 0u }; s < 2; ++s) {
      // get particle properties
      auto& species = domain.species[s];
      auto  i1      = species.i1;
      auto  dx1     = species.dx1;
      auto  tag     = species.tag;  
    
      Kokkos::parallel_for(
          "RemoveParticles",
          species.rangeActiveParticles(),
          Lambda(index_t p) {
            // check if the particle is already dead
            if (tag(p) == ParticleTag::dead) {
              return;
            }
            // convert particle position to grid coordinates
            const auto x_Cd = static_cast<real_t>(i1(p)) +
                              static_cast<real_t>(dx1(p));
            // convert grid coordinates to physical coordinates
            const auto x_Ph = mesh.metric.template convert<1, Crd::Cd, Crd::XYZ>(
              x_Cd);
            
            // if the particle position is to the right of xmin, tag it as dead
            if (x_Ph > xmin) {
              tag(p) = ParticleTag::dead;
            }
          });
      }

    /*
      Reset the fields inside the purged region
    */
    // define indices range to reset fields
    // (not including ghost zones in either direction)
    boundaries_t<bool> incl_ghosts;
    for (auto d = 0; d < M::Dim; ++d) {
      incl_ghosts.push_back({ false, false });
    }

    // define the rectangular box region where fields are reset
    boundaries_t<real_t> purge_box;
    // loop over all dimension
    for (auto d = 0u; d < M::Dim; ++d) {
      if (d == 0) {
        purge_box.push_back({ xmin, global_xmax });
      } else {
        purge_box.push_back(Range::All);
      }
    }

    // convert physical extent to a range of cells
    const auto extent = domain.mesh.ExtentToRange(purge_box, incl_ghosts);
    // record the range min/max boundaries in each dimension
    tuple_t<std::size_t, M::Dim> x_min { 0 }, x_max { 0 };
    for (auto d = 0; d < M::Dim; ++d) {
      x_min[d] = extent[d].first;
      x_max[d] = extent[d].second;
    }

    Kokkos::parallel_for("ResetFields",
                         CreateRangePolicy<M::Dim>(x_min, x_max),
                         arch::SetEMFields_kernel<decltype(init_flds), S, M> {
                           domain.fields.em,
                           init_flds,
                           domain.mesh.metric });

  }
};
```

1. because we essentially remove the particles, the returned E-fields must have zero divergence.
