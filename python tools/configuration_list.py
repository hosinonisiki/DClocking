from chip_configuration import *

# Configuration list
default_configuration = ChipConfiguration('default', 0)
default_configuration.instantiation_head = ['-- Module unplugged']
default_configuration.instantiation_tail = []
default_configuration.port_signals = {}
default_configuration.fmc_name = None # Decided runtime
default_configuration.fmc_id = None # Decided runtime
default_configuration.fmc_type = "lpc"
default_configuration.fmc_configuration = {
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
FL9781_configuration.fmc_id = None # Decided runtime
FL9781_configuration.fmc_type = "lpc"
FL9781_configuration.fmc_configuration = {
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
FL1010_configuration.fmc_id = None # Decided runtime
FL1010_configuration.fmc_type = "lpc"
FL1010_configuration.fmc_configuration = {
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
FL9627_configuration.fmc_id = None # Decided runtime
FL9627_configuration.fmc_type = "lpc"
FL9627_configuration.fmc_configuration = {
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
    '    adc_ext_clk => open,\n', \
    '    sys_rst => sys_rst,\n'
]
FL9613_configuration.instantiation_tail = [');\n']
FL9613_configuration.port_signals = {
    'adc_a_b_data_fmc' : 'std_logic_vector(11 downto 0)', \
    'adc_c_d_data_fmc' : 'std_logic_vector(11 downto 0)', \
    'adc_a_b_dco_fmc' : 'std_logic', \
    'adc_c_d_dco_fmc' : 'std_logic', \
    'adc_ad_sync_fmc' : 'std_logic', \
    'adc_clk_sync_fmc' : 'std_logic', \
    'adc_clk_reset_fmc' : 'std_logic', \
    'adc_a_b_spi_ss_fmc' : 'std_logic', \
    'adc_c_d_spi_ss_fmc' : 'std_logic', \
    'adc_clk_spi_ss_fmc' : 'std_logic', \
    'adc_spi_sck_fmc' : 'std_logic', \
    'adc_spi_mosi_fmc' : 'std_logic', \
    'adc_a_b_spi_miso_fmc' : 'std_logic', \
    'adc_c_d_spi_miso_fmc' : 'std_logic', \
    'adc_clk_spi_miso_fmc' : 'std_logic', \
    'adc_spi_io_tri_fmc' : 'std_logic', \
    'adc_ext_clk_fmc' : 'std_logic', \
    'adc_eeprom_iic_scl_fmc' : 'std_logic', \
    'adc_eeprom_iic_sda_fmc' : 'std_logic'
}
FL9613_configuration.fmc_name = None # Decided runtime
FL9613_configuration.fmc_id = None # Decided runtime
FL9613_configuration.fmc_type = "lpc"
FL9613_configuration.fmc_configuration = {
    'clk0': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'is_clock': True },
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
    { 'signal_name': 'adc_ext_clk_fmc', 'index': None, 'pin': 'clk0', 'pin_suffix': '' },
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
    { 'signal_name': 'adc_ad_sync_fmc', 'index': None, 'pin': 'la15', 'pin_suffix': '_n' },
    { 'signal_name': 'adc_clk_sync_fmc', 'index': None, 'pin': 'la16', 'pin_suffix': '_n' },
    { 'signal_name': 'adc_clk_reset_fmc', 'index': None, 'pin': 'la33', 'pin_suffix': '_p' },
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

# Congiguration for FH8052
FH8052_configuration = ChipConfiguration('FH8052', 5)
FH8052_configuration.instantiation_head = [
    'FH8052 : entity work.FH8052_adapter port map(\n', \
    '    adc_a_data => adc_buf(<natural>),\n', \
    '    adc_b_data => adc_buf(<natural>),\n', \
    '    dac_a_data => dac_buf(<natural>),\n', \
    '    dac_b_data => dac_buf(<natural>),\n', \
    '    sys_clk_250M => sys_clk,\n', \
    '    sys_clk_125M => sys_clk_125M,\n', \
    '    sys_rst => sys_rst,\n', \
    '    spi_ss => spi_ss(<SPI_SS_INDEX>),\n', \
    '    spi_sck => spi_sclk,\n', \
    '    spi_mosi => spi_mosi,\n', \
    '    spi_miso => spi_miso_buf(<SPI_MISO_BUF_INDEX>),\n', \
    '    spi_io_tri => spi_io_tri,\n', \
    '    ref_clk_p => ref_clk_p,\n', \
    '    ref_clk_n => ref_clk_n,\n'
]
FH8052_configuration.instantiation_tail = [');\n']
FH8052_configuration.port_signals = {
    'tx_ref_clk_p_fmc' : 'std_logic', \
    'tx_ref_clk_n_fmc' : 'std_logic', \
    'rx_ref_clk_p_fmc' : 'std_logic', \
    'rx_ref_clk_n_fmc' : 'std_logic', \
    'tx_sysref_fmc' : 'std_logic', \
    'rx_sysref_fmc' : 'std_logic', \
    'tx_sync_fmc' : 'std_logic', \
    'rx_sync_fmc' : 'std_logic', \
    'txp_out_fmc' : 'std_logic_vector(3 downto 0)', \
    'txn_out_fmc' : 'std_logic_vector(3 downto 0)', \
    'rxp_in_fmc' : 'std_logic_vector(3 downto 0)', \
    'rxn_in_fmc' : 'std_logic_vector(3 downto 0)', \
    'tx_core_clk_p_fmc' : 'std_logic', \
    'tx_core_clk_n_fmc' : 'std_logic', \
    'rx_core_clk_p_fmc' : 'std_logic', \
    'rx_core_clk_n_fmc' : 'std_logic', \
    'adc_spi_ss_fmc' : 'std_logic', \
    'dac_spi_ss_fmc' : 'std_logic', \
    'clk_spi_ss_fmc' : 'std_logic', \
    'spi_sck_fmc' : 'std_logic', \
    'spi_mosi_fmc' : 'std_logic', \
    'adc_spi_miso_fmc' : 'std_logic', \
    'dac_spi_miso_fmc' : 'std_logic', \
    'clk_spi_miso_fmc' : 'std_logic', \
    'spi_io_tri_fmc' : 'std_logic', \
    'adc_fda_fmc' : 'std_logic', \
    'adc_fdb_fmc' : 'std_logic', \
    'adc_pwdn_fmc' : 'std_logic', \
    'dac_irq_fmc' : 'std_logic', \
    'dac_rstn_fmc' : 'std_logic', \
    'dac_txen_fmc' : 'std_logic', \
    'clk_status_fmc' : 'std_logic_vector(0 to 1)', \
    'eeprom_iic_scl_fmc' : 'std_logic', \
    'eeprom_iic_sda_fmc' : 'std_logic' \
}
FH8052_configuration.fmc_name = None # Decided runtime
FH8052_configuration.fmc_id = None # Decided runtime
FH8052_configuration.fmc_type = "hpc"
FH8052_configuration.fmc_configuration = {
    'clk0': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'clk1': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la00': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la01': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'out', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la02': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la03': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la04': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la05': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la06': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la07': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la08': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la09': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'inout', 'is_clock': False, 'is_clock_n': False },
    'la10': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la11': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la12': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la13': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la14': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la15': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la16': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la17': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la18': { 'is_differential': True, 'used_as_single_ended': False, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la19': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la20': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la21': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la22': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la23': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'inout', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la24': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la25': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la26': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la27': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'inout', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la28': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la29': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la30': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la31': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la32': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la33': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'scl': { 'is_differential': False, 'io_type': 'out', 'is_clock': False },
    'sda': { 'is_differential': False, 'io_type': 'out', 'is_clock': False },
    'ha00': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha01': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha02': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha03': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha04': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha05': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha06': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha07': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha08': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha09': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha10': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha11': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha12': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha13': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha14': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha15': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha16': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha17': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha18': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha19': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha20': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha21': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha22': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'ha23': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'hb00': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'hb01': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'hb02': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'hb03': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'hb04': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'hb05': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'hb06': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'hb07': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'hb08': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'hb09': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'hb10': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'hb11': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'gbt0': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'gbt1': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'dp0_m2c': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'dp1_m2c': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'dp2_m2c': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'dp3_m2c': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'dp0_c2m': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'dp1_c2m': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'dp2_c2m': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'dp3_c2m': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False }
}
FH8052_configuration.signal_mapping = [
    { 'signal_name': 'tx_ref_clk_p_fmc', 'index': None, 'pin': 'gbt1', 'pin_suffix': '_p' },
    { 'signal_name': 'tx_ref_clk_n_fmc', 'index': None, 'pin': 'gbt1', 'pin_suffix': '_n' },
    { 'signal_name': 'rx_ref_clk_p_fmc', 'index': None, 'pin': 'gbt0', 'pin_suffix': '_p' },
    { 'signal_name': 'rx_ref_clk_n_fmc', 'index': None, 'pin': 'gbt0', 'pin_suffix': '_n' },
    { 'signal_name': 'tx_sysref_fmc', 'index': None, 'pin': 'la04', 'pin_suffix': '' },
    { 'signal_name': 'rx_sysref_fmc', 'index': None, 'pin': 'la03', 'pin_suffix': '' },
    { 'signal_name': 'tx_sync_fmc', 'index': None, 'pin': 'la18', 'pin_suffix': '' },
    { 'signal_name': 'rx_sync_fmc', 'index': None, 'pin': 'la01', 'pin_suffix': '' },
    { 'signal_name': 'txp_out_fmc', 'index': 0, 'pin': 'dp0_c2m', 'pin_suffix': '_p' },
    { 'signal_name': 'txn_out_fmc', 'index': 0, 'pin': 'dp0_c2m', 'pin_suffix': '_n' },
    { 'signal_name': 'txp_out_fmc', 'index': 1, 'pin': 'dp1_c2m', 'pin_suffix': '_p' },
    { 'signal_name': 'txn_out_fmc', 'index': 1, 'pin': 'dp1_c2m', 'pin_suffix': '_n' },
    { 'signal_name': 'txp_out_fmc', 'index': 2, 'pin': 'dp2_c2m', 'pin_suffix': '_p' },
    { 'signal_name': 'txn_out_fmc', 'index': 2, 'pin': 'dp2_c2m', 'pin_suffix': '_n' },
    { 'signal_name': 'txp_out_fmc', 'index': 3, 'pin': 'dp3_c2m', 'pin_suffix': '_p' },
    { 'signal_name': 'txn_out_fmc', 'index': 3, 'pin': 'dp3_c2m', 'pin_suffix': '_n' },
    { 'signal_name': 'rxp_in_fmc', 'index': 0, 'pin': 'dp0_m2c', 'pin_suffix': '_p' },
    { 'signal_name': 'rxn_in_fmc', 'index': 0, 'pin': 'dp0_m2c', 'pin_suffix': '_n' },
    { 'signal_name': 'rxp_in_fmc', 'index': 1, 'pin': 'dp1_m2c', 'pin_suffix': '_p' },
    { 'signal_name': 'rxn_in_fmc', 'index': 1, 'pin': 'dp1_m2c', 'pin_suffix': '_n' },
    { 'signal_name': 'rxp_in_fmc', 'index': 2, 'pin': 'dp2_m2c', 'pin_suffix': '_p' },
    { 'signal_name': 'rxn_in_fmc', 'index': 2, 'pin': 'dp2_m2c', 'pin_suffix': '_n' },
    { 'signal_name': 'rxp_in_fmc', 'index': 3, 'pin': 'dp3_m2c', 'pin_suffix': '_p' },
    { 'signal_name': 'rxn_in_fmc', 'index': 3, 'pin': 'dp3_m2c', 'pin_suffix': '_n' },
    { 'signal_name': 'tx_core_clk_p_fmc', 'index': None, 'pin': 'la17', 'pin_suffix': '_p' },
    { 'signal_name': 'tx_core_clk_n_fmc', 'index': None, 'pin': 'la17', 'pin_suffix': '_n' },
    { 'signal_name': 'rx_core_clk_p_fmc', 'index': None, 'pin': 'la00', 'pin_suffix': '_p' },
    { 'signal_name': 'rx_core_clk_n_fmc', 'index': None, 'pin': 'la00', 'pin_suffix': '_n' },
    { 'signal_name': 'adc_spi_ss_fmc', 'index': None, 'pin': 'la05', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_spi_ss_fmc', 'index': None, 'pin': 'la13', 'pin_suffix': '_n' },
    { 'signal_name': 'clk_spi_ss_fmc', 'index': None, 'pin': 'la14', 'pin_suffix': '_n' },
    { 'signal_name': 'spi_sck_fmc', 'index': None, 'pin': 'la05', 'pin_suffix': '_p' },
    { 'signal_name': 'spi_sck_fmc', 'index': None, 'pin': 'la13', 'pin_suffix': '_p' },
    { 'signal_name': 'spi_sck_fmc', 'index': None, 'pin': 'la14', 'pin_suffix': '_p' },
    { 'signal_name': 'spi_mosi_fmc', 'index': None, 'pin': 'la09', 'pin_suffix': '_no' },
    { 'signal_name': 'spi_mosi_fmc', 'index': None, 'pin': 'la23', 'pin_suffix': '_po' },
    { 'signal_name': 'spi_mosi_fmc', 'index': None, 'pin': 'la27', 'pin_suffix': '_po' },
    { 'signal_name': 'adc_spi_miso_fmc', 'index': None, 'pin': 'la09', 'pin_suffix': '_ni' },
    { 'signal_name': 'dac_spi_miso_fmc', 'index': None, 'pin': 'la23', 'pin_suffix': '_pi' },
    { 'signal_name': 'clk_spi_miso_fmc', 'index': None, 'pin': 'la27', 'pin_suffix': '_pi' },
    { 'signal_name': 'spi_io_tri_fmc', 'index': None, 'pin': 'la09', 'pin_suffix': '_nt' },
    { 'signal_name': 'spi_io_tri_fmc', 'index': None, 'pin': 'la23', 'pin_suffix': '_pt' },
    { 'signal_name': 'spi_io_tri_fmc', 'index': None, 'pin': 'la27', 'pin_suffix': '_pt' },
    { 'signal_name': 'adc_fda_fmc', 'index': None, 'pin': 'la06', 'pin_suffix': '_p' },
    { 'signal_name': 'adc_fdb_fmc', 'index': None, 'pin': 'la06', 'pin_suffix': '_n' },
    { 'signal_name': 'adc_pwdn_fmc', 'index': None, 'pin': 'la09', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_irq_fmc', 'index': None, 'pin': 'la27', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_rstn_fmc', 'index': None, 'pin': 'la26', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_txen_fmc', 'index': None, 'pin': 'la26', 'pin_suffix': '_n' },
    { 'signal_name': 'clk_status_fmc', 'index': 0, 'pin': 'la07', 'pin_suffix': '_p' },
    { 'signal_name': 'clk_status_fmc', 'index': 1, 'pin': 'la07', 'pin_suffix': '_n' },
    { 'signal_name': 'eeprom_iic_scl_fmc', 'index': None, 'pin': 'scl', 'pin_suffix': '' },
    { 'signal_name': 'eeprom_iic_sda_fmc', 'index': None, 'pin': 'sda', 'pin_suffix': '' }
]

# Configuration for FH9767D
FH9767D_configuration = ChipConfiguration('FH9767D', 6)
FH9767D_configuration.instantiation_head = [
    'FH9767D : entity work.FH9767D_adapter port map(\n', \
    '    dac_a_data => dac_buf(<natural>),\n', \
    '    dac_b_data => dac_buf(<natural>),\n', \
    '    dac_c_data => dac_buf(<natural>),\n', \
    '    dac_d_data => dac_buf(<natural>),\n', \
    '    sys_clk => sys_clk,\n', \
    '    dac_clk_125M => sys_clk_125M,\n', \
    '    sys_rst => sys_rst,\n'
]
FH9767D_configuration.instantiation_tail = [');\n']
FH9767D_configuration.port_signals = {
    'dac_a_data_fmc' : 'std_logic_vector(13 downto 0)', \
    'dac_b_data_fmc' : 'std_logic_vector(13 downto 0)', \
    'dac_c_data_fmc' : 'std_logic_vector(13 downto 0)', \
    'dac_d_data_fmc' : 'std_logic_vector(13 downto 0)', \
    'dac_a_wrt_fmc' : 'std_logic', \
    'dac_b_wrt_fmc' : 'std_logic', \
    'dac_c_wrt_fmc' : 'std_logic', \
    'dac_d_wrt_fmc' : 'std_logic', \
    'dac_a_clk_fmc' : 'std_logic', \
    'dac_b_clk_fmc' : 'std_logic', \
    'dac_c_clk_fmc' : 'std_logic', \
    'dac_d_clk_fmc' : 'std_logic' \
}
FH9767D_configuration.fmc_name = None # Decided runtime
FH9767D_configuration.fmc_id = None # Decided runtime
FH9767D_configuration.fmc_type = "lpc"
FH9767D_configuration.fmc_configuration = {
    'clk0': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'clk1': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la00': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': True, 'is_clock_n': False },
    'la01': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': True, 'is_clock_n': False },
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
    'la17': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': True, 'is_clock_n': False },
    'la18': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': True, 'is_clock_n': False },
    'la19': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la20': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la21': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la22': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la23': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la24': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la25': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la26': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la27': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'in', 'io_type_n': 'in', 'is_clock': False, 'is_clock_n': False },
    'la28': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la29': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la30': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la31': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la32': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'la33': { 'is_differential': True, 'used_as_single_ended': True, 'io_type': 'out', 'io_type_n': 'out', 'is_clock': False, 'is_clock_n': False },
    'scl': { 'is_differential': False, 'io_type': 'in', 'is_clock': False },
    'sda': { 'is_differential': False, 'io_type': 'in', 'is_clock': False }
}
FH9767D_configuration.signal_mapping = [
    { 'signal_name': 'dac_a_data_fmc', 'index': 0, 'pin': 'la07', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_a_data_fmc', 'index': 1, 'pin': 'la07', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_a_data_fmc', 'index': 2, 'pin': 'la08', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_a_data_fmc', 'index': 3, 'pin': 'la08', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_a_data_fmc', 'index': 4, 'pin': 'la05', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_a_data_fmc', 'index': 5, 'pin': 'la06', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_a_data_fmc', 'index': 6, 'pin': 'la04', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_a_data_fmc', 'index': 7, 'pin': 'la04', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_a_data_fmc', 'index': 8, 'pin': 'la03', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_a_data_fmc', 'index': 9, 'pin': 'la03', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_a_data_fmc', 'index': 10, 'pin': 'la05', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_a_data_fmc', 'index': 11, 'pin': 'la06', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_a_data_fmc', 'index': 12, 'pin': 'la02', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_a_data_fmc', 'index': 13, 'pin': 'la02', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_b_data_fmc', 'index': 0, 'pin': 'la14', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_b_data_fmc', 'index': 1, 'pin': 'la14', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_b_data_fmc', 'index': 2, 'pin': 'la13', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_b_data_fmc', 'index': 3, 'pin': 'la13', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_b_data_fmc', 'index': 4, 'pin': 'la16', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_b_data_fmc', 'index': 5, 'pin': 'la16', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_b_data_fmc', 'index': 6, 'pin': 'la10', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_b_data_fmc', 'index': 7, 'pin': 'la09', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_b_data_fmc', 'index': 8, 'pin': 'la10', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_b_data_fmc', 'index': 9, 'pin': 'la11', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_b_data_fmc', 'index': 10, 'pin': 'la11', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_b_data_fmc', 'index': 11, 'pin': 'la09', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_b_data_fmc', 'index': 12, 'pin': 'la12', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_b_data_fmc', 'index': 13, 'pin': 'la12', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_c_data_fmc', 'index': 0, 'pin': 'la25', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_c_data_fmc', 'index': 1, 'pin': 'la25', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_c_data_fmc', 'index': 2, 'pin': 'la21', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_c_data_fmc', 'index': 3, 'pin': 'la21', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_c_data_fmc', 'index': 4, 'pin': 'la22', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_c_data_fmc', 'index': 5, 'pin': 'la22', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_c_data_fmc', 'index': 6, 'pin': 'la23', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_c_data_fmc', 'index': 7, 'pin': 'la23', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_c_data_fmc', 'index': 8, 'pin': 'la20', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_c_data_fmc', 'index': 9, 'pin': 'la19', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_c_data_fmc', 'index': 10, 'pin': 'la19', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_c_data_fmc', 'index': 11, 'pin': 'la20', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_c_data_fmc', 'index': 12, 'pin': 'la15', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_c_data_fmc', 'index': 13, 'pin': 'la15', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_d_data_fmc', 'index': 0, 'pin': 'la32', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_d_data_fmc', 'index': 1, 'pin': 'la32', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_d_data_fmc', 'index': 2, 'pin': 'la33', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_d_data_fmc', 'index': 3, 'pin': 'la33', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_d_data_fmc', 'index': 4, 'pin': 'la30', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_d_data_fmc', 'index': 5, 'pin': 'la30', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_d_data_fmc', 'index': 6, 'pin': 'la31', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_d_data_fmc', 'index': 7, 'pin': 'la31', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_d_data_fmc', 'index': 8, 'pin': 'la29', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_d_data_fmc', 'index': 9, 'pin': 'la28', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_d_data_fmc', 'index': 10, 'pin': 'la28', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_d_data_fmc', 'index': 11, 'pin': 'la29', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_d_data_fmc', 'index': 12, 'pin': 'la24', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_d_data_fmc', 'index': 13, 'pin': 'la24', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_a_wrt_fmc', 'index': None, 'pin': 'la00', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_b_wrt_fmc', 'index': None, 'pin': 'la01', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_c_wrt_fmc', 'index': None, 'pin': 'la18', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_d_wrt_fmc', 'index': None, 'pin': 'la17', 'pin_suffix': '_n' },
    { 'signal_name': 'dac_a_clk_fmc', 'index': None, 'pin': 'la00', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_b_clk_fmc', 'index': None, 'pin': 'la01', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_c_clk_fmc', 'index': None, 'pin': 'la18', 'pin_suffix': '_p' },
    { 'signal_name': 'dac_d_clk_fmc', 'index': None, 'pin': 'la17', 'pin_suffix': '_p' }
]