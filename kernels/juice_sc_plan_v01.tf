KPL/FK

Frame (FK) kernel file for JUICE Spacecraft Planning frame mapping
===============================================================================

   This frames kernel overwrites the JUICE spacecraft frame (JUICE_SPACECRAFT)
   definition from [3] and maps it to the JUICE spacecraft planning frame
   (JUICE_SPACECRAFT_PLAN) defined in [3].
   
   This allows the user to use the existing alignments and instrument frame
   definitions in the JUICE frames kernel (see ref [3]) to perform instrument
   specific mission analysis and attitude dependent science opportunity
   identification using the so-called planning CKs. Please refer to the
   section ``Using this frame'' for further details.
   
   NOTE THAT BY USING THIS KERNEL, THE JUICE_SPACECRAFT FRAME WILL BE 
   MAPPED TO THE JUICE_SPACECRAFT_PLAN FRAME, AND ANY CK PROVIDING
   ORIENTATION FOR THE JUICE_SPACECRAFT FRAME WILL NOT BE USED BY THE
   APPLICATION SOFTWARE, EVEN IF IT IS LOADED IN THE KERNEL POOL.
   
   
Version and Date
-------------------------------------------------------------------------------

   Version 0.1 -- October 21, 2022 -- Marc Costa Sitja, ESAC/ESA
   
      Initial version.
      

References
-------------------------------------------------------------------------------

   [1]   "Frames Required Reading"
   
   [2]   "Kernel Pool Required Reading"
   
   [3]   JUICE Frames Definition Kernel (FK), latest version.

         
Contact Information
-------------------------------------------------------------------------------

   If you have any questions regarding this file contact the
   ESA SPICE Service (ESS) at ESAC:

           Alfredo Escalante Lopez
           (+34) 91-8131-429
           spice@sciops.esa.int

   or the JUICE Science Operations Center at ESAC:

           Marc Costa Sitja
           (+34) 646-746-711
           Marc.Costa@ext.esa.int
           

Implementation Notes
-------------------------------------------------------------------------------

   This file is used by the SPICE system as follows: programs that make use
   of this frame kernel must "load" the kernel normally during program
   initialization. Loading the kernel associates the data items with
   their names in a data structure called the "kernel pool".  The SPICELIB
   routine FURNSH loads a kernel into the pool as shown below:

     FORTRAN: (SPICELIB)

       CALL FURNSH ( frame_kernel_name )

     C: (CSPICE)

       furnsh_c ( frame_kernel_name );

     IDL: (ICY)

       cspice_furnsh, frame_kernel_name

     MATLAB: (MICE)

          cspice_furnsh ( 'frame_kernel_name' )

     PYTHON: (SPICEYPY)*

          furnsh( frame_kernel_name )

   In order for a program or routine to extract data from the pool, the
   SPICELIB routines GDPOOL, GIPOOL, and GCPOOL are used.  See [2] for
   more details.

   This file was created and may be updated with a text editor or word
   processor.

   * SPICEYPY is a non-official, community developed Python wrapper for the
     NAIF SPICE toolkit. Its development is managed on Github.
     It is available at: https://github.com/AndrewAnnex/SpiceyPy
   

Using this frame
-------------------------------------------------------------------------------

   This frames have been implemented to overwrite the JUICE_SPACECRAFT
   frame definition provided in the JUICE Frames Definitions kernel ([3])
   and map it to the JUICE_SPACECRAFT_PLAN frame defined in the JUICE
   Frames Definitions kernel ([3]).
   
   In order to make use of this frames kernel, this file MUST BE LOADED
   AFTER the JUICE frames definition kernel.
   
   A metakernel defined to use this file should look like this:
      
         ...
         
              $DATA/fk/juice_v01.tf
              $DATA/fk/juice_sc_plan_v01.tf
         
         ...
         
   (*) the example presents version 0.1 of the JUICE frames kernel.
       Newer versions of these files will produce the same results.
   
   NOTE THAT BY USING THIS KERNEL, THE JUICE_SPACECRAFT FRAME WILL BE 
   MAPPED TO THE JUICE_SPACECRAFT_PLAN FRAME, AND ANY CK PROVIDING
   ORIENTATION FOR THE JUICE_SPACECRAFT_MEAS FRAME WILL NOT BE USED BY
   THE APPLICATION SOFTWARE, EVEN IF IT IS LOADED IN THE KERNEL POOL.


  \begindata
  
      FRAME_-28000_CLASS        = 4
      TKFRAME_-28000_RELATIVE   = 'JUICE_SPACECRAFT_PLAN'
      TKFRAME_-28000_SPEC       = 'MATRIX'
      TKFRAME_-28000_MATRIX     = ( 1   0   0
                                    0   1   0
                                    0   0   1 )
   
  \begintext


End of FK file.