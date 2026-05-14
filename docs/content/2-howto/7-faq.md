---
hide:
  - footer
---

# F.A.Q.

!!! abstract "tl;dr"

    Here we collect the most frequent questions that might occur. Please, make sure to inspect this section before filing a GitHub issue.

## Code usage

!!! faq "I want to have a custom boundary/injection/driving/distribution function/output."
    
    All of that *can* be done via the tools provided by the problem generator. Please inspect carefully the [section dedicated to that](../2-howto/1-problem_generators.md). Also have a look at the set of officially supported problem generators some of which might implement a variation of what your original intent is.

## Technical


!!! faq "Running in a `docker` container with an AMD card"

    AMD has a vary [brief documentation](https://rocm.docs.amd.com/projects/install-on-linux/en/latest/how-to/docker.html) on the topic. In theory the `docker` containers that come with the code should work. Just make sure you have the proper groups (`render` and `video`) defined and added to the current user. If it complains about access to `/dev/kfd`, You might have to run docker as a root.


!!! faq "Compilation errors"
    
    Before merging with the released stable version, the code is tested on CUDA and HIP GPU compilers, as well as few version of CPU compilers (GCC 9...11, and LLVM 13...17). If you are encountering compiler errors on GPUs, first thing to check is whether the compilers are set up properly (i.e., whether CMake indeed captures the right compilers). Here are a few tips:

    - CUDA @ NVIDIA GPUs: make sure you have a version of `gcc` which is supported by the version of CUDA you are using; check out [this unofficial compatibility matrix](https://gist.github.com/ax3l/9489132#nvcc). In particular, Intel compilers are not very compatible with CUDA, and it is recommended to use `gcc` instead (you won't gain much by using Intel anyway, since CUDA will be doing the heavy-lifting).
  
    - HIP/ROCm @ AMD GPUs: ROCm library is a headache. The documentation is even more so. Below is our best attempt to outline how to configure things on an AMD card.


        1. Make sure you have the ROCm library loaded: e.g., run `rocminfo`;
        2. Sometimes the environment variables are not properly set up, so make sure you have the following variables properly defined: 

        - `CMAKE_PREFIX_PATH=/opt/rocm` (or wherever ROCm is installed),
        - `CC=hipcc` & `CXX=hipcc`,
        - in rare occasions, you might have to also explicitly pass `-D CMAKE_CXX_COMPILER=clang++` to cmake during the configuration stage;

        3. Compile the code with proper Kokkos flags; i.e., for MI250x GPUs you would use: `-D Kokkos_ENABLE_HIP=ON` and `-D Kokkos_ARCH_AMD_GFX90A=ON`.

        Now running is a bit trickier and the exact instruction might vary from machine to machine (part of it is because ROCm is much less streamlined than CUDA, but also system administrators on clusters are often more negligent towards AMD GPUs). 

        * If you are running this on a cluster -- the first thing to do is to inspect the documentation of the cluster. There you might find the proper `slurm` command for requesting GPU nodes and binding each GPU to respective CPUs. 

        * On personal machines figuring this out is a bit easier. First, inspect the output of `rocminfo` and `rocm-smi`. From there, you should be able to find the ID of the GPU you want to use. If you see more than one device -- that means you either have an additional AMD CPU, or an integrated GPU installed as well; ignore them. You will need to override two environment variables:

        - `HSA_OVERRIDE_GFX_VERSION` set to GFX version that you used to compile the code (if you used `GFX1100` Kokkos flag, that would be `11.0.0`);
        - `HIP_VISIBLE_DEVICES`, and `ROCR_VISIBLE_DEVICES` both need to be set to your device ID (usually, it's just a number from 0 to the number of devices that support HIP).

        For example, the output of `rocminfo | grep -A 5 "Agent "` may look like this:
        ```
        Agent 1                  
        *******                  
          Name:                    AMD Ryzen 9 7940HS w/ Radeon 780M Graphics
          Uuid:                    CPU-XX                             
          Marketing Name:          AMD Ryzen 9 7940HS w/ Radeon 780M Graphics
          Vendor Name:             CPU                                
        --
        Agent 2                  
        *******                  
          Name:                    gfx1100                            
          Uuid:                    GPU-XX                             
          Marketing Name:          AMD Radeon™ RX 7700S             
          Vendor Name:             AMD                                
        --
        Agent 3                  
        *******                  
          Name:                    gfx1100                            
          Uuid:                    GPU-XX                             
          Marketing Name:          AMD Radeon Graphics                
          Vendor Name:             AMD
        ```
        In this case, the required GPU is the `Agent 2`, which supports GFX1100. `rocm-smi` will look something like this:
        ```
        ============================================ ROCm System Management Interface ============================================
        ====================================================== Concise Info ======================================================
        Device  Node  IDs              Temp    Power    Partitions          SCLK  MCLK     Fan    Perf  PwrCap       VRAM%  GPU%  
                      (DID,     GUID)  (Edge)  (Avg)    (Mem, Compute, ID)                                                        
        ==========================================================================================================================
        0       1     0x7480,   19047  35.0°C  0.0W     N/A, N/A, 0         0Mhz  96Mhz    29.8%  auto  100.0W       0%     0%    
        1       2     0x15bf,   17218  48.0°C  19.111W  N/A, N/A, 0         None  1000Mhz  0%     auto  Unsupported  82%    5%    
        ==========================================================================================================================
        ================================================== End of ROCm SMI Log ===================================================
        ```
        so the GPU we need has `Device` ID of `0` (since it's the dedicated GPU, it might automatically turn off when idle to save power on laptops; hence `Power = 0.0W`). Now we can run the code with: 
        ```sh
        HSA_OVERRIDE_GFX_VERSION=11.0.0 HIP_VISIBLE_DEVICES=0 ROCR_VISIBLE_DEVICES=0 ./executable ...
        ```



!!! faq "If the code gives an error, how do I know whether the problem is with the Entity itself or with the other libraries it depends on (e.g., `Kokkos`, `ADIOS2`, `MPI`)?"
  
    One good way of narrowing the problem down, is to run the so-called minimal examples, provided in the directory called `minimal/` in the source. It has detailed instructions on how to compile these examples, and should hopefully be able to verify whether all the installed dependencies work as expected, before looking for an issue in the Entity itself. 

    Another good way is to compile the code with `-D TESTS=ON` flag, which will compile all the unit tests, and you can [run them one-by-one](../1-getting-started/1-compile-run.md#testing). You may also compile the tests also with various flags, e.g., `-D mpi=ON`, `-D output=ON`, `-D precision=double`.
