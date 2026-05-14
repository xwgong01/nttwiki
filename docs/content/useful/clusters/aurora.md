[`Aurora`](https://docs.alcf.anl.gov/aurora/) uses [Intel PVC](https://www.intel.com/content/www/us/en/products/sku/232873/intel-data-center-gpu-max-1550/specifications.html) nodes with 6 GPUs/node. Each PVC has 128GB of memory and is split into 2 tiles. It is recommended to use 1 MPI rank per tile, so 2 per GPU and 12 per node.
Development of entity for `Aurora` is currently ongoing. Use the following docs with caution and check in with `@LudwigBoess` on potential changes.

**Modules to load**

You can load the installed dependencies with

```sh
module load cmake
module load adios2/2.11.0-cpu
module load kokkos/5.0.1-sycl
```

I would recommend saving the module configuration for easy loading within the PBS job:
```sh
module save entity
```

You can compile `entity` with:

```sh
cmake -B build -D pgen=<your_pgen> -D precision=single -D mpi=ON -D gpu_aware_mpi=OFF -D output=ON -DCMAKE_C_COMPILER=mpicc -DCMAKE_CXX_COMPILER=mpicxx
```

Please note that `gpu_aware_mpi=OFF` is critical at the moment, we hope to fix this in a future release.

**Running entity**

Aurora uses [PBS](https://docs.alcf.anl.gov/running-jobs/?h=pbs) for workload management.
The Intel PVC GPUs are split into two tiles each and it is recommended to launch one MPI rank per tile.

```sh
#!/bin/bash -l
#PBS -A <project_name>
#PBS -N <job_name>
#PBS -l select=1                # number of nodes to use
#PBS -l walltime=00:05:00
#PBS -l filesystems=flare       # replace with the filesystem of your project
#PBS -k doe
#PBS -l place=scatter
#PBS -q debug

NTOTRANKS=12        # 2*6*N_nodes - updated with your requested number
NRANKS_PER_NODE=12  # 2*6  - always the same

# change to directory from which job was submitted
cd $PBS_O_WORKDIR

# load all modules defined above
module restore entity

# only relevant for CPU pinning and to avoid Kokkos complaints
export OMP_PROC_BIND=spread

mpiexec --envall -n ${NTOTRANKS} --ppn ${NRANKS_PER_NODE} ./gpu_tile_compact.sh ./entity.xc -input weibel.toml
```

To run it you need to define a script `gpu_tile_compact.sh` in the same folder as your executable. It should look like this:

```sh
#!/bin/bash -l
num_gpu=6
num_tile=2
gpu_id=$(( (PALS_LOCAL_RANKID / num_tile ) % num_gpu ))
tile_id=$((PALS_LOCAL_RANKID % num_tile))
export ZE_ENABLE_PCI_ID_DEVICE_ORDER=1
export ZE_AFFINITY_MASK=$gpu_id.$tile_id

# reports the GPU tile pinning
echo “RANK= $PALS_RANKID LOCAL_RANK= $PALS_LOCAL_RANKID gpu= $gpu_id.$tile_id”
# runs the actual job
exec "$@"
```
