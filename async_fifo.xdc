# set_property SCOPED_TO_CELLS [get_cells -hierarchical -filter {ORIG_REF_NAME == xil_defaultlib_async_fifo}] [get_files async_fifo.xdc]

set_false_path -from [get_pins -of_objects [get_cells -hierarchical -filter {ORIG_REF_NAME =~ FD* && PARENT =~ *async_fifo_inst*}]] -to [get_pins -of_objects [get_cells full_1_reg]]
set_false_path -from [get_pins -of_objects [get_cells -hierarchical -filter {ORIG_REF_NAME =~ FD* && PARENT =~ *async_fifo_inst*}]] -to [get_pins -of_objects [get_cells empty_1_reg]]