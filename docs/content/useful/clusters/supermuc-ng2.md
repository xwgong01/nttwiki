[`SuperMUC-NG2`](https://docs.alcf.anl.gov/aurora/) uses [Intel PVC](https://www.intel.com/content/www/us/en/products/sku/232873/intel-data-center-gpu-max-1550/specifications.html) nodes with 4 GPUs/node. Each PVC has 128GB of memory and is split into 2 tiles. It is recommended to use 1 MPI rank per tile, so 2 per GPU and 8 per node.
Development of entity for `SuperMUC` is currently ongoing. Use the following docs with caution and check in with `@LudwigBoess` on potential changes.

**Modules to load**

You can load the installed dependencies with

```sh
module sw stack/24.6.0
module load cmake
module load intel/2025.3.0
module load intel-mpi/2021.17.0 
module load kokkos/5.0.00
module load adios2/2.11.0
```

**Running entity**

This is an example SLURM script:

```sh
#!/bin/bash
#SBATCH -J weibel
#SBATCH -o ./log/%N.%j.out
#SBATCH -D .
#SBATCH --partition=test
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=8   # one task per tile
#SBATCH --account=<project>
#SBATCH --export=none
#SBATCH --time=00:30:00

module load slurm_setup

export I_MPI_OFFLOAD=1 
export I_MPI_OFFLOAD_RDMA=1 
export I_MPI_OFFLOAD_FAST_MEMCPY_COLL=1 
export PSM3_RDMA=1 
export PSM3_GPUDIRECT=0 # this will hopefully be fixed in the future

# this is just for debugging reasons
export I_MPI_DEBUG=5

export OMP_PROC_BIND=spread 
export OMP_PLACES=threads
export OMP_NUM_THREADS=8

export ZE_FLAT_DEVICE_HIERARCHY=FLAT
export ONEAPI_DEVICE_SELECTOR=level_zero:gpu

# print configuration as sanit check
mpiexec ./entity.xc --kokkos-print-configuration -input weibel.toml

```
