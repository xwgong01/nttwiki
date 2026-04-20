['Frontier'](https://docs.olcf.ornl.gov/systems/frontier_user_guide.html#system-overview) is a HPE Cray EX supercomputer.
The system has 77 Olympus rack HPE cabinets, each with 128 AMD compute nodes, and a total of 9,856 AMD compute nodes.
Each node has 8 GPUs,each having 64 GB of high-bandwidth memory (HBM2E). 

**Installing the dependencies**

The list of required modules is 

```sh
module load PrgEnv-cray
module load cmake
module load rocm
module load cray-mpich
module load craype-accel-amd-gfx90a
```

**Compiling & running the code**

Even though the documentaion states that the MPI implementation is Cray’s MPICH, which is “GPU-aware", it seems to be bugged,
so you will always need to add the flag `gpu_aware_mpi=OFF`.

Your `cmake` setting should look something like this:
```sh
cmake -B build \
  -D pgen=<PGEN> \
  -D mpi=ON \
  -D Kokkos_ENABLE_HIP=ON \
  -D Kokkos_ARCH_AMD_GFX90A=ON \
  -D CMAKE_CXX_COMPILER=hipcc \
  -D CMAKE_C_COMPILER=hipcc \
  -D gpu_aware_mpi=OFF \
  -D CMAKE_CXX_FLAGS="-Wno-c++11-narrowing -munsafe-fp-atomics" \
  -D CMAKE_C_FLAGS="-Wno-c++11-narrowing -munsafe-fp-atomics"
```

The queue policies encourage users to run jobs on Frontier that are as large as possible. To that end, OLCF implements queue policies that enable large jobs to run in a timely fashion:

| Bin | Min Nodes | Max Nodes | Max Walltime (Hours) | Aging Boost (Days) |
| --- | --------- | --------- | -------------------- | ------------------ |
| 1   | 5,645     | 9,472     | 12.0                 | 8                  |
| 2   | 1,882     | 5,644     | 12.0                 | 4                  |
| 3   | 184       | 1,881     | 12.0                 | 0                  |
| 4   | 92        | 183       | 6.0                  | 0                  |
| 5   | 1         | 91        | 2.0                  | 0                  |

Jobs are aged according to the job’s requested node count (older age equals higher queue priority). 

Finally an example `SLURM` script using the full node looks like this:

```slurm
#!/bin/bash
#SBATCH -A <YOUR_PROJECT_ID>
#SBATCH -J entity_prod
#SBATCH -o entity_prod_%j.out
#SBATCH -t 12:00:00
#SBATCH -p batch
#SBATCH -N 184

module load PrgEnv-cray
module load cmake
module load rocm
module load cray-mpich
module load craype-accel-amd-gfx90a

srun -N184 -n1472 -c1 --gpus-per-task=1 --gpu-bind=closest ./entity -input <INPUT>.toml
```
For post-processing and visualization it is possible to use `extended` partition. This allows to have 24-Hour maximum wall time with 64-Node maximum job size.

```slurm
#!/bin/bash
#SBATCH -A <YOUR_PROJECT_ID>
#SBATCH -J entity_postproc
#SBATCH -o entity_postproc_%j.out
#SBATCH -t 06:00:00
#SBATCH -p extended
#SBATCH -N 1

module load cray-python
source ~/.venv/bin/activate

python3 <your_script.py>
```