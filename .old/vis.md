
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

Now simply import the `nt2` module and load the output data:

```python
import nt2

data = nt2.Data("MySimulation")
```

1. Note, that even though the `h5` file can be quite large, the data is loaded lazily, so the memory consumption is minimal; data chunks are only loaded when they are actually needed for the analysis or visualization.

### Accessing fields

Data selection is conveniently done with the `sel` and `isel` methods for the `xarray` Datasets ([more info](https://docs.xarray.dev/en/stable/user-guide/indexing.html)). For example, to select the `Rho` field around physical time `t=98`, one can do:

```python
data.fields.Rho.sel(t=98, method="nearest") # (1)!
```

1. The `method="nearest"` is used to select the closest time step to the requested time.

![nt2demo1](../../assets/images/howto/nt2-demo-1.png){width=50% align=right class="invertlight"} 

We can then plot the selected data using the `plot` method of the `xarray` Dataset:

```python
data.fields.Rho\
  .sel(t=98, method="nearest")\
  .plot(
    norm=mpl.colors.Normalize(0, 1e2),  # (2)!
    cmap="jet") # (1)!
```

1. The `norm` and `cmap` arguments are used to set the colorbar limits and the colormap just like in normal `matplotlib` context.
2. Make sure to also `module load matplotlib as mpl`.

If the resolution is too high, one can also coarsen the data before plotting:

```python
data.fields.Rho\
  .sel(t=98, method="nearest")\
  .coarsen(x=16, y=4).mean()\
  .plot(
    norm=mpl.colors.Normalize(0, 1e2),
    cmap="jet")
```

or downsample:

```python
data.fields.Rho\
  .sel(t=98, method="nearest")\
  .isel(x=slice(None, None, 16), y=slice(None, None, 4))\ # (1)!
  .plot(
    norm=mpl.colors.Normalize(0, 1e2),
    cmap="jet")
```

1. The difference between `isel` and `sel` is that `isel` uses the integer indices along the given dimension, while `sel` uses the physical coordinates.

![nt2demo2](../../assets/images/howto/nt2-demo-2.png){width=50% align=right class="invertlight"} 

One can also do more complicated things, such as building a 1D plot of the evolution of the mean $B^2$ in the box:

```python
data.fields.Bx**2 + data.fields.By**2 + data.fields.Bz**2\
  .mean(("x", "y"))\
  .plot()
```

or make "waterfall" plots, collapsing the quantity along one of the axis, and plotting vs the other axis and time:

```python
(data.fields.Rho_2 - data.fields.Rho_1)\
  .mean("x")\
  .plot(yincrease=False)
```

Particles and spectra can, in turn, be accessed via `data.particles[s]`, where `s` is the species index, and `data.spectra`.


!!! code "`nt2py` documentation"

    You can access the documentation of the `nt2py` functions and methods of the `Data` object by calling `nt2.<function>?` in the jupyter notebook or `help(nt2.<function>)` in the python console.

### Accessing particles

Particles are stored in the same `data` object and are lazily preloaded when one calls `nt2.Data(...)`, as we did above. To access the particle data, use `data.particles`, which returns a custom object which can then be converted into an explicitly populated dataframe using the `load()` method. Selection of particles can be done in a similar way to the fields:

```python
data.particles.sel(t=slice(None, 10)).sel(sp=[1, 3], id=[123, 456, 789]).load()
```

which selects all times before $t<10$, selects species 1 and 3, and picks specific particle id-s (traced along all preselected times). There are two built-in plotting methods: `.spectrum_plot`, and `.phase_plot`, for plotting a 1D energy distribution function of each species, and a 2D phase-space plot (or any 2D binned plot). 

```python
data.particles.sel(t=10).spectrum_plot(
    bins=np.logspace(0, 3), 
    quantity=lambda df: np.sqrt(1 + df.ux**2 + df.uy**2 + df.uz**2),
)

data.particles.sel(t=10).phase_plot(
    x_quantity=lambda df: df.x,
    y_quantity=lambda df: df.ux,
    xy_bins=(np.linspace(-1, 1), np.linspace(0, 2)),
)
```

You may, however, simply use the data from the dataframe to make the plots directly:

```python
df = data.particles.sel(t=10, method="nearest").load()
plt.scatter(df.x, df.y, colors=df.sp) # color by species
```

??? showplot "scatter plot $\{x,~y\}$"

    ![nt2demo3](../../assets/images/howto/nt2-demo-3.png){class="invertlight"}

!!! code "`isel` indexing"

    `isel(t=-1)` selects the last time step.

### Accessing runtime spectra

Distribution functions for all particle species in the box are also written with the data at specified timesteps. These can be accessed via `data.spectra`, which has several different fields. As in particles & fields, you can access the data at different times using `data.spectra.isel(t=...)` or `data.spectra.sel(t=...)`. The energy bins are written into `data.spectra.E`; by default, the binning is done logarithmically in $\gamma - 1$ for massive particles and energy, $E$, for the photons. Below is an example script to build a distribution function of electron-positron pairs at output step `t=450`:

```python
sp = data.spectra.isel(t=450)

plt.figure(figsize=(6, 3))
plt.xscale("log")
plt.yscale("log")
plt.plot(sp.E, sp.N_1 + sp.N_2, c="r")
plt.ylim(10, 3e5)
plt.xlabel(r"$\gamma - 1$")
plt.xlim(sp.E.min(), sp.E.max())
```

???+ showplot "particle spectra"

    ![nt2demo5](../../assets/images/howto/nt2-demo-5.png){ class="invertlight" }

---

### Exporting movies

To produce animations, `nt2py` provides a shortcut helper function which saves the frames using multiple threads, and then calls `ffmpeg` to merge them into a video file. 

```python
def plot_frame(ti, data):
    # function must take two parameters:
    # - ti: output index
    # - data: the dataset loaded with nt2.read
    #
    # any type data manipulation & plotting routine goes here
    # e.g.
    fig = plt.figure()
    ax = fig.add_subplot(111)
    (data.fields.N_1 + data.fields.N_2).isel(t=ti).plot(ax=ax, cmap="viridis")
    #                                        ^
    #                           selecting timestep by index

# then simply pass this function to the routine:
data.makeMovie(plot_frame, num_cpus=8, framerate="10", ...)
#                                   ^
#                 (optional) by default all available threads are used
```

`makeMovie` also accepts a number of arguments used by `ffmpeg`, such as the framerate, the compression rate, etc. Run the following to see all the arguments:

```python
import nt2.export as nt2e
nt2e.makeMovie?
```
