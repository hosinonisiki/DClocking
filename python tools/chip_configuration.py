class ChipConfiguration:
    iotype2suffix = {'in': '_b', 'out': '_b', 'inout': '_b'} # Port suffix are kept the same for the convenience of physical constraints
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.instantiation_head = None # Beginning of instantiation code
        '''
        example: * Note that the following code must be stored as list of strings
        FL9627 : entity work.FL9627_adapter port map(
            adc_a_data => adc_a_data_buf,
            adc_b_data => adc_b_data_buf,
            adc_c_data => adc_c_data_buf,
            adc_d_data => adc_d_data_buf,
            adc_a_b_spi_ss => adc_a_b_spi_ss,
            adc_c_d_spi_ss => adc_c_d_spi_ss,
            adc_spi_sck => spi_sclk,
            adc_spi_mosi => spi_mosi,
            adc1_spi_miso => adc1_spi_miso,
            adc2_spi_miso => adc2_spi_miso,
            adc_spi_io_tri => spi_io_tri,
            sys_clk => sys_clk,
            adc_clk_125M => sys_clk_125M,
            sys_rst => sys_rst,
        '''
        self.instantiation_tail = None # End of instantiation code
        '''
        example:
        );
        '''
        self.port_signals = None # Dictionary of port signals, will be inserted in the middle of instantiation code and used in signal declaration
        '''
        example:
        ['adc_a_b_data' : 'std_logic_vector(13 downto 0)',
        'adc_c_d_data' : 'std_logic_vector(13 downto 0)',
        'adc_a_b_dco' : 'std_logic',
        'adc_c_d_dco' : 'std_logic',
        'adc_a_b_spi_ss' : 'std_logic',
        'adc_c_d_spi_ss' : 'std_logic',
        'adc_spi_sck' : 'std_logic',
        'adc_spi_mosi' : 'std_logic',
        'adc1_spi_miso' : 'std_logic',
        'adc2_spi_miso' : 'std_logic',
        'adc_spi_io_tri' : 'std_logic',
        'adc_clk_125M' : 'std_logic',
        'adc_eeprom_iic_scl' : 'std_logic',
        'adc_eeprom_iic_sda' : 'std_logic']
        '''

        self.lpc_name = None
        self.lpc_id = None
        self.lpc_configuration = None # Configuration of the LPC
        '''
        configuration format:
        {
            'name' : # port name, accepts 'clk0', 'clk1', 'la00' ... 'la33', 'scl' and 'sda'
            {
                'is_differential': <bool>, # True if the port is differential.
                'used_as_single_ended': <bool>, # True if the differential port is used as two single-ended ports. None-exist for 'scl' and 'sda'
                'io_type': <str>, # Accepts 'in', 'out' and 'inout'
                'io_type_n': <str>, # Used when a differential pin is used as two single-ended pins
                'is_clock': <bool>, # True if the port is a clock, which may require extra buffer
                'is_clock_n': <bool>, # Used when a differential pin is used as two single-ended pins
            }
        }
        '''

        self.signal_mapping = None # Mapping of port signals to lpc ports
        '''
        format:
        [
            {
                'signal_name': <str>, # Name of the signal in the top level entity
                'index': <int> | None, # Index of the signal if it is a vector element, None if it is a single bit
                'pin': <str>, # Name of the pin in the lpc_configuration
                'pin_suffix': <str> # Suffix of the pin, must be compatible with the lpc_configuration.
                # e.g. '_nt' only when the pin in question is differential but used as single-ended, while the io_type of the n side is 'inout'
                # '' when no extra suffix is needed to specify the target signal
            }
        ]
        '''
        self.make_ready = False

    def is_complete(self):
        return self.instantiation_head is not None \
            and self.instantiation_tail is not None \
            and self.port_signals is not None \
            and self.lpc_name is not None \
            and self.lpc_id is not None \
            and self.lpc_configuration is not None \
            and self.signal_mapping is not None
    
    def make(self):
        # Assert all required fields are not None
        assert self.is_complete(), 'Chip configuration is not complete'
        # Generate lpc pin declaration code
        self.pin_declaration = []
        for pin in self.lpc_configuration:
            configuration = self.lpc_configuration[pin]
            if configuration['is_differential']:
                if configuration['used_as_single_ended']:
                    self.pin_declaration.append(f'{self.lpc_name}_{pin}_p{self.iotype2suffix[configuration["io_type"]]} : {configuration["io_type"]} std_logic;' + '\n')
                    self.pin_declaration.append(f'{self.lpc_name}_{pin}_n{self.iotype2suffix[configuration["io_type_n"]]} : {configuration["io_type_n"]} std_logic;' + '\n')
                else:
                    self.pin_declaration.append(f'{self.lpc_name}_{pin}_p{self.iotype2suffix[configuration["io_type"]]} : {configuration["io_type"]} std_logic;' + '\n')
                    self.pin_declaration.append(f'{self.lpc_name}_{pin}_n{self.iotype2suffix[configuration["io_type"]]} : {configuration["io_type"]} std_logic;' + '\n')
            else:
                self.pin_declaration.append(f'{self.lpc_name}_{pin}{self.iotype2suffix[configuration["io_type"]]} : {configuration["io_type"]} std_logic;' + '\n')
        # Generate signal declaration code
        # Note that signals associated with io buffers are generated in the later step
        self.signal_declaration = []
        for signal in self.port_signals:
            self.signal_declaration.append(f'signal {signal}_buf : {self.port_signals[signal]};' + '\n')
        # Generate instantiation code
        self.instantiation_code = self.instantiation_head
        indent = ' ' * 4
        for i, signal in enumerate(self.port_signals):
            if i != len(self.port_signals) - 1:
                self.instantiation_code.append(f'{indent}{signal} => {signal}_buf,' + '\n')
            else:
                self.instantiation_code.append(f'{indent}{signal} => {signal}_buf' + '\n')
        self.instantiation_code += self.instantiation_tail
        # Replace "<SPI_SS_INDEX>" and "<SPI_MISO_BUF_INDEX>" with the actual index
        self.instantiation_code = list(map(lambda x: x.replace('<SPI_SS_INDEX>', f'{self.lpc_id * 4 - 4} to {self.lpc_id * 4 - 1}'), self.instantiation_code))
        self.instantiation_code = list(map(lambda x: x.replace('<SPI_MISO_BUF_INDEX>', f'{self.lpc_id - 1}'), self.instantiation_code))
        # Generate signal assignment code
        self.signal_assignment = []
        for mapping in self.signal_mapping:
            configuration = self.lpc_configuration[mapping['pin']]
            suffix = mapping['pin_suffix']
            if suffix == '_po' or suffix == '_pt' or suffix == '_no' or suffix == '_nt' or suffix == '_o' or suffix == '_t':
                direction = 'out'
            elif suffix == '_pi' or suffix == '_ni' or suffix == '_i':
                direction = 'in'
            elif suffix == '_p' or suffix == '':
                direction = configuration['io_type']
            elif suffix == '_n':
                direction = configuration['io_type_n']
            index_suffix = f'({mapping["index"]})' if mapping["index"] is not None else ''
            signal_name = f'{mapping["signal_name"]}_buf{index_suffix}'
            if direction == 'out':
                self.signal_assignment.append(f'{self.lpc_name}_{mapping["pin"]}{suffix} <= {signal_name};' + '\n')
            else:
                self.signal_assignment.append(f'{signal_name} <= {self.lpc_name}_{mapping["pin"]}{suffix};' + '\n')
        # Generate io buffer code
        self.io_buffer = []
        self.signal_declaration.append('\n')
        indent = ' ' * 4
        first_buffer = True
        for pin in self.lpc_configuration:
            configuration = self.lpc_configuration[pin]
            if not first_buffer:
                self.io_buffer.append('\n')
                first_buffer = False
            # Assume clock buffer only generated for single-way input
            if configuration['is_differential']:
                if configuration['used_as_single_ended']:
                    if configuration['io_type'] == 'in':
                        if configuration['is_clock']:
                            self.io_buffer.append(f'{self.lpc_name}_{pin}_p_ibuf : IBUFG port map(' + '\n')
                            self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_p{self.iotype2suffix[configuration["io_type"]]},' + '\n')
                            self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_p_buf' + '\n')
                            self.io_buffer.append(');\n')
                            self.io_buffer.append(f'{self.lpc_name}_{pin}_p_bufg : BUFG port map(' + '\n')
                            self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_p_buf,' + '\n')
                            self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_p' + '\n')
                            self.io_buffer.append(');\n')
                            self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_p_buf : std_logic;' + '\n')
                            self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_p : std_logic;' + '\n')
                        else:
                            self.io_buffer.append(f'{self.lpc_name}_{pin}_p_ibuf : IBUF port map(' + '\n')
                            self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_p{self.iotype2suffix[configuration["io_type"]]},' + '\n')
                            self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_p' + '\n')
                            self.io_buffer.append(');\n')
                            self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_p : std_logic;' + '\n')
                    elif configuration['io_type'] == 'out':
                        self.io_buffer.append(f'{self.lpc_name}_{pin}_p_obuf : OBUF port map(' + '\n')
                        self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_p,' + '\n')
                        self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_p{self.iotype2suffix[configuration["io_type"]]}' + '\n')
                        self.io_buffer.append(');\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_p : std_logic;' + '\n')
                    elif configuration['io_type'] == 'inout':
                        self.io_buffer.append(f'{self.lpc_name}_{pin}_p_iobuf : IOBUF port map(' + '\n')
                        self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_po,' + '\n')
                        self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_pi,' + '\n')
                        self.io_buffer.append(f'{indent}IO => {self.lpc_name}_{pin}_p{self.iotype2suffix[configuration["io_type"]]},' + '\n')
                        self.io_buffer.append(f'{indent}T => {self.lpc_name}_{pin}_pt' + '\n')
                        self.io_buffer.append(');\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_po : std_logic;' + '\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_pi : std_logic;' + '\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_pt : std_logic;' + '\n')
                    if configuration['io_type_n'] == 'in':
                        if configuration['is_clock_n']:
                            self.io_buffer.append(f'{self.lpc_name}_{pin}_n_ibuf : IBUFG port map(' + '\n')
                            self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_n{self.iotype2suffix[configuration["io_type_n"]]},' + '\n')
                            self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_n_buf' + '\n')
                            self.io_buffer.append(');\n')
                            self.io_buffer.append(f'{self.lpc_name}_{pin}_n_bufg : BUFG port map(' + '\n')
                            self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_n_buf,' + '\n')
                            self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_n' + '\n')
                            self.io_buffer.append(');\n')
                            self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_n_buf : std_logic;' + '\n')
                            self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_n : std_logic;' + '\n')
                        else:
                            self.io_buffer.append(f'{self.lpc_name}_{pin}_n_ibuf : IBUF port map(' + '\n')
                            self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_n{self.iotype2suffix[configuration["io_type_n"]]},' + '\n')
                            self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_n' + '\n')
                            self.io_buffer.append(');\n')
                            self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_n : std_logic;' + '\n')
                    elif configuration['io_type_n'] == 'out':
                        self.io_buffer.append(f'{self.lpc_name}_{pin}_n_obuf : OBUF port map(' + '\n')
                        self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_n,' + '\n')
                        self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_n{self.iotype2suffix[configuration["io_type_n"]]}' + '\n')
                        self.io_buffer.append(');\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_n : std_logic;' + '\n')
                    elif configuration['io_type_n'] == 'inout':
                        self.io_buffer.append(f'{self.lpc_name}_{pin}_n_iobuf : IOBUF port map(' + '\n')
                        self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_no,' + '\n')
                        self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_ni,' + '\n')
                        self.io_buffer.append(f'{indent}IO => {self.lpc_name}_{pin}_n{self.iotype2suffix[configuration["io_type_n"]]},' + '\n')
                        self.io_buffer.append(f'{indent}T => {self.lpc_name}_{pin}_nt' + '\n')
                        self.io_buffer.append(');\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_no : std_logic;' + '\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_ni : std_logic;' + '\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_nt : std_logic;' + '\n')
                elif not configuration['used_as_single_ended']: # Write the condition explicitly for clarity
                    if configuration['io_type'] == 'in':
                        if configuration['is_clock']:
                            self.io_buffer.append(f'{self.lpc_name}_{pin}_ibufds : IBUFDS port map(' + '\n')
                            self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_p{self.iotype2suffix[configuration["io_type"]]},' + '\n')
                            self.io_buffer.append(f'{indent}IB => {self.lpc_name}_{pin}_n{self.iotype2suffix[configuration["io_type"]]},' + '\n')
                            self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_buf' + '\n')
                            self.io_buffer.append(');\n')
                            self.io_buffer.append(f'{self.lpc_name}_{pin}_bufg : BUFG port map(' + '\n')
                            self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_buf,' + '\n')
                            self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}' + '\n')
                            self.io_buffer.append(');\n')
                            self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_buf : std_logic;' + '\n')
                            self.signal_declaration.append(f'signal {self.lpc_name}_{pin} : std_logic;' + '\n')
                        else:
                            self.io_buffer.append(f'{self.lpc_name}_{pin}_ibufds : IBUFDS port map(' + '\n')
                            self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_p{self.iotype2suffix[configuration["io_type"]]},' + '\n')
                            self.io_buffer.append(f'{indent}IB => {self.lpc_name}_{pin}_n{self.iotype2suffix[configuration["io_type"]]},' + '\n')
                            self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}' + '\n')
                            self.io_buffer.append(');\n')
                            self.signal_declaration.append(f'signal {self.lpc_name}_{pin} : std_logic;' + '\n')
                    elif configuration['io_type'] == 'out':
                        self.io_buffer.append(f'{self.lpc_name}_{pin}_obufds : OBUFDS port map(' + '\n')
                        self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin},' + '\n')
                        self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_p{self.iotype2suffix[configuration["io_type"]]},' + '\n')
                        self.io_buffer.append(f'{indent}OB => {self.lpc_name}_{pin}_n{self.iotype2suffix[configuration["io_type"]]}' + '\n')
                        self.io_buffer.append(');\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin} : std_logic;' + '\n')
                    elif configuration['io_type'] == 'inout':
                        self.io_buffer.append(f'{self.lpc_name}_{pin}_iobufds : IOBUFDS port map(' + '\n')
                        self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_o,' + '\n')
                        self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_i,' + '\n')
                        self.io_buffer.append(f'{indent}IO => {self.lpc_name}_{pin}_p{self.iotype2suffix[configuration["io_type"]]},' + '\n')
                        self.io_buffer.append(f'{indent}T => {self.lpc_name}_{pin}_t,' + '\n')
                        self.io_buffer.append(f'{indent}IOB => {self.lpc_name}_{pin}_n{self.iotype2suffix[configuration["io_type"]]}' + '\n')
                        self.io_buffer.append(');\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_o : std_logic;' + '\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_i : std_logic;' + '\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_t : std_logic;' + '\n')
            elif not configuration['is_differential']: # Write the condition explicitly for clarity
                if configuration['io_type'] == 'in':
                    if configuration['is_clock']:
                        self.io_buffer.append(f'{self.lpc_name}_{pin}_ibuf : IBUF port map(' + '\n')
                        self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}{self.iotype2suffix[configuration["io_type"]]},' + '\n')
                        self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_buf' + '\n')
                        self.io_buffer.append(');\n')
                        self.io_buffer.append(f'{self.lpc_name}_{pin}_bufg : BUFG port map(' + '\n')
                        self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_buf,' + '\n')
                        self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}' + '\n')
                        self.io_buffer.append(');\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_buf : std_logic;' + '\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin} : std_logic;' + '\n')
                    else:
                        self.io_buffer.append(f'{self.lpc_name}_{pin}_ibuf : IBUF port map(' + '\n')
                        self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}{self.iotype2suffix[configuration["io_type"]]},' + '\n')
                        self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}' + '\n')
                        self.io_buffer.append(');\n')
                        self.signal_declaration.append(f'signal {self.lpc_name}_{pin} : std_logic;' + '\n')
                elif configuration['io_type'] == 'out':
                    self.io_buffer.append(f'{self.lpc_name}_{pin}_obuf : OBUF port map(' + '\n')
                    self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin},' + '\n')
                    self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}{self.iotype2suffix[configuration["io_type"]]}' + '\n')
                    self.io_buffer.append(');\n')
                    self.signal_declaration.append(f'signal {self.lpc_name}_{pin} : std_logic;' + '\n')
                elif configuration['io_type'] == 'inout':
                    self.io_buffer.append(f'{self.lpc_name}_{pin}_iobuf : IOBUF port map(' + '\n')
                    self.io_buffer.append(f'{indent}I => {self.lpc_name}_{pin}_o,' + '\n')
                    self.io_buffer.append(f'{indent}O => {self.lpc_name}_{pin}_i,' + '\n')
                    self.io_buffer.append(f'{indent}IO => {self.lpc_name}_{pin}{self.iotype2suffix[configuration["io_type"]]},' + '\n')
                    self.io_buffer.append(f'{indent}T => {self.lpc_name}_{pin}_t' + '\n')
                    self.io_buffer.append(');\n')
                    self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_o : std_logic;' + '\n')
                    self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_i : std_logic;' + '\n')
                    self.signal_declaration.append(f'signal {self.lpc_name}_{pin}_t : std_logic;' + '\n')
        self.make_ready = True

    def get_code(self, part_name, format = 'string'):
        assert self.make_ready, 'Chip configuration is not ready'
        if format == 'string':
            return ''.join(self.get_code(part_name, format = 'list'))
        elif format == 'list':
            if part_name == 'pin_declaration':
                return self.pin_declaration
            elif part_name == 'signal_declaration':
                return self.signal_declaration
            elif part_name == 'instantiation_code':
                return self.instantiation_code
            elif part_name == 'signal_assignment':
                return self.signal_assignment
            elif part_name == 'io_buffer':
                return self.io_buffer
            else:
                raise ValueError(f'Unknown part name: {part_name}')
        
if __name__ == '__main__':
    # Test code
    config = ChipConfiguration('FL9627', 0)
    config.instantiation_head = ['FL9627 : entity work.FL9627_adapter port map(\n', \
                                '    adc_a_data => adc_a_data_buf,\n', \
                                '    adc_b_data => adc_b_data_buf,\n', \
                                '    adc_c_data => adc_c_data_buf,\n', \
                                '    adc_d_data => adc_d_data_buf,\n', \
                                '    adc_a_b_spi_ss => adc_a_b_spi_ss,\n', \
                                '    adc_c_d_spi_ss => adc_c_d_spi_ss,\n', \
                                '    adc_spi_sck => spi_sclk,\n', \
                                '    adc_spi_mosi => spi_mosi,\n', \
                                '    adc1_spi_miso => adc1_spi_miso,\n', \
                                '    adc2_spi_miso => adc2_spi_miso,\n', \
                                '    adc_spi_io_tri => spi_io_tri,\n', \
                                '    sys_clk => sys_clk,\n', \
                                '    adc_clk_125M => sys_clk_125M,\n', \
                                '    sys_rst => sys_rst,\n']
    config.instantiation_tail = [');\n']
    config.port_signals = {'adc_a_b_data_fmc' : 'std_logic_vector(11 downto 0)', \
                            'adc_c_d_data_fmc' : 'std_logic_vector(11 downto 0)', \
                            'adc_a_b_dco_fmc' : 'std_logic', \
                            'adc_c_d_dco_fmc' : 'std_logic', \
                            'adc_a_b_spi_ss_fmc' : 'std_logic', \
                            'adc_c_d_spi_ss_fmc' : 'std_logic', \
                            'adc_spi_sck_fmc' : 'std_logic', \
                            'adc_spi_mosi_fmc' : 'std_logic', \
                            'adc1_spi_miso_fmc' : 'std_logic', \
                            'adc2_spi_miso_fmc' : 'std_logic', \
                            'adc_spi_io_tri_fmc' : 'std_logic', \
                            'adc_clk_125M_fmc' : 'std_logic', \
                            'adc_eeprom_iic_scl_fmc' : 'std_logic', \
                            'adc_eeprom_iic_sda_fmc' : 'std_logic'
                            }
    config.lpc_name = 'fmc3_hpc'
    config.lpc_id = 3
    config.lpc_configuration = {
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
        'scl': { 'is_differential': False, 'used_as_single_ended': True, 'io_type': 'out', 'is_clock': False },
        'sda': { 'is_differential': False, 'used_as_single_ended': True, 'io_type': 'out', 'is_clock': False }
    }

    config.signal_mapping = [
        { 'signal_name': 'clk_125M_fmc', 'index': None, 'pin': 'la01', 'pin_suffix': '_p' },
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
        { 'signal_name': 'clk_125M_fmc', 'index': None, 'pin': 'la17', 'pin_suffix': '_p' },
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
        { 'signal_name': 'adc1_spi_miso_fmc', 'index': None, 'pin': 'la03', 'pin_suffix': '_ni' },
        { 'signal_name': 'adc2_spi_miso_fmc', 'index': None, 'pin': 'la23', 'pin_suffix': '_pi' },
        { 'signal_name': 'adc_eeprom_iic_scl_fmc', 'index': None, 'pin': 'scl', 'pin_suffix': '' },
        { 'signal_name': 'adc_eeprom_iic_sda_fmc', 'index': None, 'pin': 'sda', 'pin_suffix': '' },
        { 'signal_name': 'adc_spi_io_tri_fmc', 'index': None, 'pin': 'la03', 'pin_suffix': '_nt' },
        { 'signal_name': 'adc_spi_io_tri_fmc', 'index': None, 'pin': 'la23', 'pin_suffix': '_pt' }
    ]
    config.make()
    print(config.get_code('pin_declaration'))
    print(config.get_code('signal_declaration'))
    print(config.get_code('instantiation_code'))
    print(config.get_code('signal_assignment'))
    print(config.get_code('io_buffer'))