Adastra is a French supercomputer hosted at CINES. 
Each accelerated (MI250X) node consists of 1 AMD EPYC 7A53 (Trento) processor with 64 cores at 2.0 GHz and 4 AMD Instinct MI250X accelerators (code name gfx90a, Aldebaran, CDNA 2 microarchitecture). This provides 64 cores (with 2 hardware threads per core) attached to 256 Gio of DDR4-3200 MHz memory and 8 Graphics Compute Dies (GCD) per node [[1]](https://dci.dci-gitlab.cines.fr/webextranet/architecture/index.html#system-overview).

**Installing the dependencies**

First clone Kokkos and ADIOS2 with the following command:

```
git clone --depth=2 --branch <version> https://github.com/kokkos/kokkos.git
git clone --depth=2 --branch <version> https://github.com/ornladios/ADIOS2.git
```

Then use the following scripts to compile. For Kokkos, first `cd kokkos`, 

```
module purge
module load cmake
module load PrgEnv-cray
module load cray-mpich
module load craype-accel-amd-gfx90a
module load rocm
# configure with
cmake -B build \
    -D CMAKE_CXX_STANDARD=20 \
    -D CMAKE_CXX_EXTENSIONS=OFF \
    -D CMAKE_CXX_COMPILER=hipcc \
    -D CMAKE_POSITION_INDEPENDENT_CODE=TRUE \
    -D Kokkos_ARCH_AMD_GFX90A=ON -D Kokkos_ENABLE_HIP=ON -D AMDGPU_TARGETS=gfx90a \
    -D CMAKE_INSTALL_PREFIX=$HOME/.entity/kokkos
# compile and install with
cmake --build build -j
cmake --install build
```

For ADIOS2, `cd ADIOS2`
```
module purge
module load cmake
module load PrgEnv-cray
module load craype-x86-genoa
module load craype-accel-amd-gfx90a
module load rocm

# configure with
cmake -B build \
    -D CMAKE_CXX_STANDARD=20 \
    -D CMAKE_CXX_EXTENSIONS=OFF \
    -D CMAKE_CXX_COMPILER=CC -D CMAKE_C_COMPILER=cc \
    -D CMAKE_POSITION_INDEPENDENT_CODE=TRUE \
    -D BUILD_SHARED_LIBS=ON \
    -D ADIOS2_USE_Python=OFF \
    -D ADIOS2_USE_Fortran=OFF \
    -D ADIOS2_USE_ZeroMQ=OFF \
    -D BUILD_TESTING=OFF \
    -D ADIOS2_BUILD_EXAMPLES=OFF \
    -D ADIOS2_USE_HDF5=OFF \
    -D ADIOS2_USE_MPI=ON \
    -D CMAKE_INSTALL_PREFIX=$HOME/.entity/adios2
# compile and install with
cmake --build build -j
cmake --install build
```

Then compile entity using the following configuration:

```
module purge
module load cmake
module load PrgEnv-cray
module load craype-x86-genoa
module load craype-accel-amd-gfx90a
module load rocm

cmake -B build \
  -D pgen=<your pgen> \
  -D mpi=ON \
  -D gpu_aware_mpi=OFF \
  -D CMAKE_C_COMPILER=cc \
  -D CMAKE_CXX_COMPILER=hipcc \
  -D MPI_C_COMPILER=mpicc \
  -D MPI_CXX_COMPILER=mpicxx \
  -D Kokkos_ENABLE_HIP=ON \
  -D Kokkos_ARCH_AMD_GFX90A=ON \
  -D CMAKE_CXX_FLAGS="--offload-arch=gfx90a -Wno-c++11-narrowing -munsafe-fp-atomics" \
  -D CMAKE_C_FLAGS="-Wno-c++11-narrowing -munsafe-fp-atomics" \
  -D Kokkos_ROOT=$HOME/.entity/kokkos/ \
  -D adios2_ROOT=$HOME/.entity/adios2/

cmake --build build -j
```

An example of the submission script looks like

```
#!/bin/bash
#SBATCH --account=<Your Billing Account>
#SBATCH --job-name="Name"
#SBATCH --constraint=MI250
#SBATCH --nodes=2
#SBATCH --exclusive
#SBATCH --time=00:30:00
#SBATCH --gpus-per-node=8

module purge
module load cmake
module load PrgEnv-cray
module load craype-x86-genoa
module load craype-accel-amd-gfx90a
module load rocm

export MPICH_GPU_SUPPORT_ENABLED=1

srun -n 16 /path_to/entity.xc -input /path_to/your.toml #-restart
```