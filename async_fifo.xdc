# Run the following command in a tcl console
# set_property SCOPED_TO_CELLS [get_cells -hierarchical -filter {ORIG_REF_NAME == async_fifo}] [get_files async_fifo.xdc]

set_max_delay -datapath_only -from [get_pins -filter {NAME =~ *C} -of_objects [get_cells -hierarchical -filter {ORIG_REF_NAME =~ FD* && PARENT =~ *async_fifo_inst*}]] -to [get_pins -filter {NAME =~ *D} -of_objects [get_cells full_1_reg]] 4
set_max_delay -datapath_only -from [get_pins -filter {NAME =~ *C} -of_objects [get_cells -hierarchical -filter {ORIG_REF_NAME =~ FD* && PARENT =~ *async_fifo_inst*}]] -to [get_pins -filter {NAME =~ *D} -of_objects [get_cells empty_1_reg]] 4