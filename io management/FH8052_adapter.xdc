set_max_delay -datapath_only -from [get_pins -filter {NAME =~ *C} -of_objects [get_cells -hierarchical -filter {NAME =~ *output_reg && PARENT =~ *sys_rst_debouncer*}]] -to [get_pins -filter {NAME =~ *D} -of_objects [get_cells -hierarchical -filter {NAME =~ *tx_rst_1_reg && PARENT =~ *FH8052*}]] 4.000
set_max_delay -datapath_only -from [get_pins -filter {NAME =~ *C} -of_objects [get_cells -hierarchical -filter {NAME =~ *output_reg && PARENT =~ *sys_rst_debouncer*}]] -to [get_pins -filter {NAME =~ *D} -of_objects [get_cells -hierarchical -filter {NAME =~ *tx_rst_2_reg && PARENT =~ *FH8052*}]] 4.000
set_max_delay -datapath_only -from [get_pins -filter {NAME =~ *C} -of_objects [get_cells -hierarchical -filter {NAME =~ *output_reg && PARENT =~ *sys_rst_debouncer*}]] -to [get_pins -filter {NAME =~ *D} -of_objects [get_cells -hierarchical -filter {NAME =~ *rx_rst_1_reg && PARENT =~ *FH8052*}]] 4.000
set_max_delay -datapath_only -from [get_pins -filter {NAME =~ *C} -of_objects [get_cells -hierarchical -filter {NAME =~ *output_reg && PARENT =~ *sys_rst_debouncer*}]] -to [get_pins -filter {NAME =~ *D} -of_objects [get_cells -hierarchical -filter {NAME =~ *rx_rst_2_reg && PARENT =~ *FH8052*}]] 4.000










