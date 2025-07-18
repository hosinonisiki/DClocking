from chip_configuration import *

# Configuration list
default_configuration = ChipConfiguration('default', 0)
default_configuration.instantiation_head = ['-- Module unplugged']
default_configuration.instantiation_tail = []
default_configuration.port_signals = {}
default_configuration.fmc_name = None # Decided runtime
default_configuration.fmc_id = None # Decided runtime
default_configuration.lpc_configuration = {
    'clk0': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'clk1': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la00': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la01': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la02': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la03': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la04': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la05': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la06': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la07': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la08': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la09': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la10': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la11': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la12': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la13': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la14': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la15': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la16': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la17': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la18': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la19': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la20': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la21': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la22': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la23': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la24': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la25': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la26': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la27': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la28': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la29': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la30': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la31': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la32': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la33': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'scl': { 'is_differential': False, 'io_type': 'in', 'is_clock': False },
    'sda': { 'is_differential': False, 'io_type': 'in', 'is_clock': False }
}
default_configuration.signal_mapping = []

# Configuration for FL9781
FL9781_configuration = ChipConfiguration('FL9781', 1)
FL9781_configuration.instantiation_head = [
    'FL9781 : entity work.FL9781_adapter port map(\n', \
    '    dac_a_data => dac_buf(<natural>),\n', \
    '    dac_b_data => dac_buf(<natural>),\n', \
    '    dac_c_data => dac_buf(<natural>),\n', \
    '    dac_d_data => dac_buf(<natural>),\n', \
    '    dac_spi_ss => spi_ss(<SPI_SS_INDEX>),\n', \
    '    dac_spi_sck => spi_sclk,\n', \
    '    dac_spi_mosi => spi_mosi,\n', \
    '    dac_spi_miso => dac_spi_miso,\n', \
    '    sys_clk => sys_clk,\n', \
    '    sys_rst => sys_rst,\n'
]
FL9781_configuration.instantiation_tail = [');\n']
FL9781_configuration.port_signals = {
    'dac_a_b_data_fmc' : 'std_logic_vector(13 downto 0)', \
    'dac_c_d_data_fmc' : 'std_logic_vector(13 downto 0)', \
    'dac_a_b_dco_fmc' : 'std_logic', \
    'dac_c_d_dco_fmc' : 'std_logic', \
    'dac_a_b_dci_fmc' : 'std_logic', \
    'dac_c_d_dci_fmc' : 'std_logic', \
    'dac_a_b_spi_ss_fmc' : 'std_logic', \
    'dac_c_d_spi_ss_fmc' : 'std_logic', \
    'dac_clk_spi_ss_fmc' : 'std_logic', \
    'dac_spi_sck_fmc' : 'std_logic', \
    'dac_spi_mosi_fmc' : 'std_logic', \
    'dac_spi_miso_fmc' : 'std_logic', \
    'dac_eeprom_iic_scl_fmc' : 'std_logic', \
    'dac_eeprom_iic_sda_fmc' : 'std_logic'
}
FL9781_configuration.fmc_name = None # Decided runtime
default_configuration.fmc_id = None # Decided runtime
FL9781_configuration.lpc_configuration = {
    'clk0': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'clk1': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la00': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': True },
    'la01': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': True },
    'la02': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la03': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la04': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la05': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la06': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la07': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la08': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la09': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la10': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la11': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la12': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la13': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la14': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la15': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la16': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la17': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': True },
    'la18': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': True },
    'la19': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la20': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la21': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la22': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la23': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la24': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la25': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la26': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la27': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la28': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la29': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la30': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la31': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la32': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'la33': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': False },
    'scl': { 'is_differential': False, 'io_type': 'out', 'is_clock': False },
    'sda': { 'is_differential': False, 'io_type': 'out', 'is_clock': False }
}
FL9781_configuration.signal_mapping = [
    { 'signal_name': 'dac_a_b_dci_fmc', 'index': None, 'pin': 'la01', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_dco_fmc', 'index': None, 'pin': 'la00', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_data_fmc', 'index': 0, 'pin': 'la16', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_data_fmc', 'index': 1, 'pin': 'la14', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_data_fmc', 'index': 2, 'pin': 'la15', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_data_fmc', 'index': 3, 'pin': 'la13', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_data_fmc', 'index': 4, 'pin': 'la11', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_data_fmc', 'index': 5, 'pin': 'la12', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_data_fmc', 'index': 6, 'pin': 'la10', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_data_fmc', 'index': 7, 'pin': 'la09', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_data_fmc', 'index': 8, 'pin': 'la07', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_data_fmc', 'index': 9, 'pin': 'la08', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_data_fmc', 'index': 10, 'pin': 'la05', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_data_fmc', 'index': 11, 'pin': 'la04', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_data_fmc', 'index': 12, 'pin': 'la03', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_data_fmc', 'index': 13, 'pin': 'la06', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_dci_fmc', 'index': None, 'pin': 'la18', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_dco_fmc', 'index': None, 'pin': 'la17', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_data_fmc', 'index': 0, 'pin': 'la30', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_data_fmc', 'index': 1, 'pin': 'la32', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_data_fmc', 'index': 2, 'pin': 'la33', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_data_fmc', 'index': 3, 'pin': 'la31', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_data_fmc', 'index': 4, 'pin': 'la28', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_data_fmc', 'index': 5, 'pin': 'la29', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_data_fmc', 'index': 6, 'pin': 'la27', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_data_fmc', 'index': 7, 'pin': 'la24', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_data_fmc', 'index': 8, 'pin': 'la25', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_data_fmc', 'index': 9, 'pin': 'la26', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_data_fmc', 'index': 10, 'pin': 'la21', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_data_fmc', 'index': 11, 'pin': 'la22', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_data_fmc', 'index': 12, 'pin': 'la23', 'pin_suffix': '' },
    { 'signal_name': 'dac_c_d_data_fmc', 'index': 13, 'pin': 'la19', 'pin_suffix': '' },
    { 'signal_name': 'dac_a_b_spi_ss_fmc', 'index': None, 'pin': 'la20', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_c_d_spi_ss_fmc', 'index': None, 'pin': 'la20', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_clk_spi_ss_fmc', 'index': None, 'pin': 'clk1', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_spi_sck_fmc', 'index': None, 'pin': 'clk1', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_spi_mosi_fmc', 'index': None, 'pin': 'clk0', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_spi_miso_fmc', 'index': None, 'pin': 'clk0', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_eeprom_iic_scl_fmc', 'index': None, 'pin': 'scl', 'pin_suffix': '' },
    { 'signal_name': 'dac_eeprom_iic_sda_fmc', 'index': None, 'pin': 'sda', 'pin_suffix': '' }
]

# Configuration for FL1010
FL1010_configuration = ChipConfiguration('FL1010', 2)
FL1010_configuration.instantiation_head = [
    'FL1010 : entity work.FL1010_adapter port map(\n', \
    '    j2_40p => j2_40p,\n', \
    '    j3_40p => j3_40p,\n'
]
FL1010_configuration.instantiation_tail = [');\n']
FL1010_configuration.port_signals = {
    'j2_40p_fmc' : 'std_logic_vector(3 to 36)', \
    'j3_40p_fmc' : 'std_logic_vector(3 to 36)', \
    'lpc240p_eeprom_iic_scl_fmc' : 'std_logic', \
    'lpc240p_eeprom_iic_sda_fmc' : 'std_logic'
}
FL1010_configuration.fmc_name = None # Decided runtime
default_configuration.fmc_id = None # Decided runtime
FL1010_configuration.lpc_configuration = {
    'clk0': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'clk1': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la00': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la01': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la02': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la03': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la04': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la05': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la06': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la07': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la08': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la09': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la10': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la11': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la12': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la13': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la14': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la15': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la16': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la17': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la18': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la19': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la20': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la21': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la22': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la23': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la24': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la25': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la26': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la27': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la28': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la29': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la30': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la31': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la32': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la33': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'scl': { 'is_differential': False, 'io_type': 'out', 'is_clock': False },
    'sda': { 'is_differential': False, 'io_type': 'out', 'is_clock': False }
}
FL1010_configuration.signal_mapping = [
    { 'signal_name': 'j2_40p_fmc', 'index': 3, 'pin': 'la17', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 4, 'pin': 'la17', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 5, 'pin': 'la18', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 6, 'pin': 'la18', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 7, 'pin': 'la23', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 8, 'pin': 'la23', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 9, 'pin': 'la26', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 10, 'pin': 'la26', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 11, 'pin': 'la27', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 12, 'pin': 'la27', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 13, 'pin': 'la28', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 14, 'pin': 'la28', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 15, 'pin': 'la29', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 16, 'pin': 'la29', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 17, 'pin': 'la24', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 18, 'pin': 'la24', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 19, 'pin': 'la25', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 20, 'pin': 'la25', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 21, 'pin': 'la21', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 22, 'pin': 'la21', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 23, 'pin': 'la22', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 24, 'pin': 'la22', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 25, 'pin': 'la31', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 26, 'pin': 'la31', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 27, 'pin': 'la30', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 28, 'pin': 'la30', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 29, 'pin': 'la33', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 30, 'pin': 'la33', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 31, 'pin': 'la32', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 32, 'pin': 'la32', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 33, 'pin': 'la19', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 34, 'pin': 'la19', 'pin_suffix': '_p' },
    { 'signal_name': 'j2_40p_fmc', 'index': 35, 'pin': 'la20', 'pin_suffix': '_n' },
    { 'signal_name': 'j2_40p_fmc', 'index': 36, 'pin': 'la20', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 3, 'pin': 'la15', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 4, 'pin': 'la15', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 5, 'pin': 'la16', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 6, 'pin': 'la16', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 7, 'pin': 'la11', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 8, 'pin': 'la11', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 9, 'pin': 'la00', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 10, 'pin': 'la00', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 11, 'pin': 'la02', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 12, 'pin': 'la02', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 13, 'pin': 'la03', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 14, 'pin': 'la03', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 15, 'pin': 'la12', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 16, 'pin': 'la12', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 17, 'pin': 'la07', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 18, 'pin': 'la07', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 19, 'pin': 'la08', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 20, 'pin': 'la08', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 21, 'pin': 'la04', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 22, 'pin': 'la04', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 23, 'pin': 'la14', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 24, 'pin': 'la14', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 25, 'pin': 'la13', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 26, 'pin': 'la13', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 27, 'pin': 'la09', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 28, 'pin': 'la09', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 29, 'pin': 'la10', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 30, 'pin': 'la10', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 31, 'pin': 'la05', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 32, 'pin': 'la05', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 33, 'pin': 'la06', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 34, 'pin': 'la06', 'pin_suffix': '_p' },
    { 'signal_name': 'j3_40p_fmc', 'index': 35, 'pin': 'la01', 'pin_suffix': '_n' },
    { 'signal_name': 'j3_40p_fmc', 'index': 36, 'pin': 'la01', 'pin_suffix': '_p' },
    { 'signal_name': 'lpc240p_eeprom_iic_scl_fmc', 'index': None, 'pin': 'scl', 'pin_suffix': '' },
    { 'signal_name': 'lpc240p_eeprom_iic_sda_fmc', 'index': None, 'pin': 'sda', 'pin_suffix': '' }
]

# Configuration for FL9627
FL9627_configuration = ChipConfiguration('FL9627', 3)
FL9627_configuration.instantiation_head = [
    'FL9627 : entity work.FL9627_adapter port map(\n', \
    '    adc_a_data => adc_buf(<natural>),\n', \
    '    adc_b_data => adc_buf(<natural>),\n', \
    '    adc_c_data => adc_buf(<natural>),\n', \
    '    adc_d_data => adc_buf(<natural>),\n', \
    '    adc_spi_ss => spi_ss(<SPI_SS_INDEX>),\n', \
    '    adc_spi_sck => spi_sclk,\n', \
    '    adc_spi_mosi => spi_mosi,\n', \
    '    adc_spi_miso => spi_miso_buf(<SPI_MISO_BUF_INDEX>),\n', \
    '    adc_spi_io_tri => spi_io_tri,\n', \
    '    sys_clk => sys_clk,\n', \
    '    adc_clk_125M => sys_clk_125M,\n', \
    '    sys_rst => sys_rst,\n'
]
FL9627_configuration.instantiation_tail = [');\n']
FL9627_configuration.port_signals = {
    'adc_a_b_data_fmc' : 'std_logic_vector(11 downto 0)', \
    'adc_c_d_data_fmc' : 'std_logic_vector(11 downto 0)', \
    'adc_a_b_dco_fmc' : 'std_logic', \
    'adc_c_d_dco_fmc' : 'std_logic', \
    'adc_a_b_spi_ss_fmc' : 'std_logic', \
    'adc_c_d_spi_ss_fmc' : 'std_logic', \
    'adc_spi_sck_fmc' : 'std_logic', \
    'adc_spi_mosi_fmc' : 'std_logic', \
    'adc_a_b_spi_miso_fmc' : 'std_logic', \
    'adc_c_d_spi_miso_fmc' : 'std_logic', \
    'adc_spi_io_tri_fmc' : 'std_logic', \
    'adc_clk_125M_fmc' : 'std_logic', \
    'adc_eeprom_iic_scl_fmc' : 'std_logic', \
    'adc_eeprom_iic_sda_fmc' : 'std_logic'
}
FL9627_configuration.fmc_name = None # Decided runtime
default_configuration.fmc_id = None # Decided runtime
FL9627_configuration.lpc_configuration = {
    'clk0': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'clk1': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la00': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': True },
    'la01': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': True, 'is_clock_n': False },
    'la02': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la03': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'inout', 'is_clock': False, 'is_clock_n': False },
    'la04': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la05': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la06': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la07': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la08': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la09': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la10': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la11': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la12': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la13': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la14': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la15': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la16': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la17': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': True, 'is_clock_n': False },
    'la18': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': True },
    'la19': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la20': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la21': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la22': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la23': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'inout', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la24': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la25': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la26': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la27': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la28': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la29': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la30': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la31': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la32': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la33': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'scl': { 'is_differential': False, 'io_type': 'out', 'is_clock': False },
    'sda': { 'is_differential': False, 'io_type': 'out', 'is_clock': False }
}
FL9627_configuration.signal_mapping = [
    { 'signal_name': 'adc_clk_125M_fmc', 'index': None, 'pin': 'la01', 'pin_suffix': '_p' },
    { 'signal_name': 'adc_a_b_dco_fmc', 'index': None, 'pin': 'la00', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 0, 'pin': 'la02', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 1, 'pin': 'la06', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 2, 'pin': 'la05', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 3, 'pin': 'la04', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 4, 'pin': 'la10', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 5, 'pin': 'la08', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 6, 'pin': 'la07', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 7, 'pin': 'la09', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 8, 'pin': 'la12', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 9, 'pin': 'la11', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 10, 'pin': 'la13', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 11, 'pin': 'la14', 'pin_suffix': '' },
    { 'signal_name': 'adc_clk_125M_fmc', 'index': None, 'pin': 'la17', 'pin_suffix': '_p' },
    { 'signal_name': 'adc_c_d_dco_fmc', 'index': None, 'pin': 'la18', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 0, 'pin': 'la20', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 1, 'pin': 'la19', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 2, 'pin': 'la27', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 3, 'pin': 'la22', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 4, 'pin': 'la21', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 5, 'pin': 'la26', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 6, 'pin': 'la25', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 7, 'pin': 'la24', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 8, 'pin': 'la29', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 9, 'pin': 'la28', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 10, 'pin': 'la31', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 11, 'pin': 'la30', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_spi_ss_fmc', 'index': None, 'pin': 'la03', 'pin_suffix': '_p' },
    { 'signal_name': 'adc_c_d_spi_ss_fmc', 'index': None, 'pin': 'la17', 'pin_suffix': '_n' },
    { 'signal_name': 'adc_spi_sck_fmc', 'index': None, 'pin': 'la01', 'pin_suffix': '_n' },
    { 'signal_name': 'adc_spi_sck_fmc', 'index': None, 'pin': 'la23', 'pin_suffix': '_n' },
    { 'signal_name': 'adc_spi_mosi_fmc', 'index': None, 'pin': 'la03', 'pin_suffix': '_no' },
    { 'signal_name': 'adc_spi_mosi_fmc', 'index': None, 'pin': 'la23', 'pin_suffix': '_po' },
    { 'signal_name': 'adc_a_b_spi_miso_fmc', 'index': None, 'pin': 'la03', 'pin_suffix': '_ni' },
    { 'signal_name': 'adc_c_d_spi_miso_fmc', 'index': None, 'pin': 'la23', 'pin_suffix': '_pi' },
    { 'signal_name': 'adc_eeprom_iic_scl_fmc', 'index': None, 'pin': 'scl', 'pin_suffix': '' },
    { 'signal_name': 'adc_eeprom_iic_sda_fmc', 'index': None, 'pin': 'sda', 'pin_suffix': '' },
    { 'signal_name': 'adc_spi_io_tri_fmc', 'index': None, 'pin': 'la03', 'pin_suffix': '_nt' },
    { 'signal_name': 'adc_spi_io_tri_fmc', 'index': None, 'pin': 'la23', 'pin_suffix': '_pt' }
]

# Configuration for FL9613
FL9613_configuration = ChipConfiguration('FL9613', 4)
FL9613_configuration.instantiation_head = [
    'FL9613 : entity work.FL9613_adapter port map(\n', \
    '    adc_a_data => adc_buf(<natural>),\n', \
    '    adc_b_data => adc_buf(<natural>),\n', \
    '    adc_c_data => adc_buf(<natural>),\n', \
    '    adc_d_data => adc_buf(<natural>),\n', \
    '    adc_spi_ss => spi_ss(<SPI_SS_INDEX>),\n', \
    '    adc_spi_sck => spi_sclk,\n', \
    '    adc_spi_mosi => spi_mosi,\n', \
    '    adc_spi_miso => spi_miso_buf(<SPI_MISO_BUF_INDEX>),\n', \
    '    adc_spi_io_tri => spi_io_tri,\n', \
    '    sys_clk => sys_clk,\n', \
    '    adc_clk_250M => sys_clk_250M,\n', \
    '    sys_rst => sys_rst,\n'
]
FL9613_configuration.instantiation_tail = [');\n']
FL9613_configuration.port_signals = {
    'adc_a_b_data_fmc' : 'std_logic_vector(11 downto 0)', \
    'adc_c_d_data_fmc' : 'std_logic_vector(11 downto 0)', \
    'adc_a_b_dco_fmc' : 'std_logic', \
    'adc_c_d_dco_fmc' : 'std_logic', \
    'adc_a_b_spi_ss_fmc' : 'std_logic', \
    'adc_c_d_spi_ss_fmc' : 'std_logic', \
    'adc_clk_spi_ss_fmc' : 'std_logic', \
    'adc_spi_sck_fmc' : 'std_logic', \
    'adc_spi_mosi_fmc' : 'std_logic', \
    'adc_a_b_spi_miso_fmc' : 'std_logic', \
    'adc_c_d_spi_miso_fmc' : 'std_logic', \
    'adc_clk_spi_miso_fmc' : 'std_logic', \
    'adc_spi_io_tri_fmc' : 'std_logic', \
    'adc_clk_250M_fmc' : 'std_logic', \
    'adc_eeprom_iic_scl_fmc' : 'std_logic', \
    'adc_eeprom_iic_sda_fmc' : 'std_logic'
}
FL9613_configuration.fmc_name = None # Decided runtime
default_configuration.fmc_id = None # Decided runtime
FL9613_configuration.lpc_configuration = {
    'clk0': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'is_clock': True },
    'clk1': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': True },
    'la00': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': True },
    'la01': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la02': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la03': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'inout', 'is_clock': False, 'is_clock_n': False },
    'la04': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la05': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la06': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la07': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la08': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la09': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la10': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la11': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la12': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la13': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la14': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la15': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'inout', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la16': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la17': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la18': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': True },
    'la19': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la20': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la21': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la22': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la23': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'inout', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': True },
    'la24': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la25': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la26': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la27': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la28': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la29': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la30': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la31': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': False },
    'la32': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': True, 'is_clock_n': False },
    'la33': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'scl': { 'is_differential': False, 'io_type': 'out', 'is_clock': False },
    'sda': { 'is_differential': False, 'io_type': 'out', 'is_clock': False }
}
FL9613_configuration.signal_mapping = [
    { 'signal_name': 'adc_clk_250M_fmc', 'index': None, 'pin': 'clk0', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_dco_fmc', 'index': None, 'pin': 'la00', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 0, 'pin': 'la02', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 1, 'pin': 'la06', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 2, 'pin': 'la05', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 3, 'pin': 'la04', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 4, 'pin': 'la10', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 5, 'pin': 'la08', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 6, 'pin': 'la07', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 7, 'pin': 'la09', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 8, 'pin': 'la12', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 9, 'pin': 'la11', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 10, 'pin': 'la13', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_data_fmc', 'index': 11, 'pin': 'la14', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_dco_fmc', 'index': None, 'pin': 'la18', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 0, 'pin': 'la20', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 1, 'pin': 'la19', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 2, 'pin': 'la27', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 3, 'pin': 'la22', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 4, 'pin': 'la21', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 5, 'pin': 'la26', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 6, 'pin': 'la25', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 7, 'pin': 'la24', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 8, 'pin': 'la29', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 9, 'pin': 'la28', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 10, 'pin': 'la31', 'pin_suffix': '' },
    { 'signal_name': 'adc_c_d_data_fmc', 'index': 11, 'pin': 'la30', 'pin_suffix': '' },
    { 'signal_name': 'adc_a_b_spi_ss_fmc', 'index': None, 'pin': 'la03', 'pin_suffix': '_p' },
    { 'signal_name': 'adc_c_d_spi_ss_fmc', 'index': None, 'pin': 'la16', 'pin_suffix': '_p' },
    { 'signal_name': 'adc_clk_spi_ss_fmc', 'index': None, 'pin': 'la32', 'pin_suffix': '_n' },
    { 'signal_name': 'adc_spi_sck_fmc', 'index': None, 'pin': 'clk1', 'pin_suffix': '_n' },
    { 'signal_name': 'adc_spi_sck_fmc', 'index': None, 'pin': 'la23', 'pin_suffix': '_n' },
    { 'signal_name': 'adc_spi_sck_fmc', 'index': None, 'pin': 'la32', 'pin_suffix': '_p' },
    { 'signal_name': 'adc_spi_mosi_fmc', 'index': None, 'pin': 'la03', 'pin_suffix': '_no' },
    { 'signal_name': 'adc_spi_mosi_fmc', 'index': None, 'pin': 'la23', 'pin_suffix': '_po' },
    { 'signal_name': 'adc_spi_mosi_fmc', 'index': None, 'pin': 'la15', 'pin_suffix': '_po' },
    { 'signal_name': 'adc_a_b_spi_miso_fmc', 'index': None, 'pin': 'la03', 'pin_suffix': '_ni' },
    { 'signal_name': 'adc_c_d_spi_miso_fmc', 'index': None, 'pin': 'la23', 'pin_suffix': '_pi' },
    { 'signal_name': 'adc_clk_spi_miso_fmc', 'index': None, 'pin': 'la15', 'pin_suffix': '_pi' },
    { 'signal_name': 'adc_eeprom_iic_scl_fmc', 'index': None, 'pin': 'scl', 'pin_suffix': '' },
    { 'signal_name': 'adc_eeprom_iic_sda_fmc', 'index': None, 'pin': 'sda', 'pin_suffix': '' },
    { 'signal_name': 'adc_spi_io_tri_fmc', 'index': None, 'pin': 'la03', 'pin_suffix': '_nt' },
    { 'signal_name': 'adc_spi_io_tri_fmc', 'index': None, 'pin': 'la23', 'pin_suffix': '_pt' },
    { 'signal_name': 'adc_spi_io_tri_fmc', 'index': None, 'pin': 'la15', 'pin_suffix': '_pt' }
]





