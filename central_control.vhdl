-- ///////////////Documentation////////////////////
-- This is the central control entity of the system.
-- It processes all input and output data from/to
-- fifo buffers, and communicates with all other
-- modules through buses.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

use work.uart_protocol.all;
use work.bus_protocol.all;

entity central_control is
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        rxd_in          :   in  std_logic_vector(7 downto 0);
        rxen_out        :   out std_logic;
        rxemp_in        :   in  std_logic;
        txd_out         :   out std_logic_vector(7 downto 0);
        txen_out        :   out std_logic;
        txful_in        :   in  std_logic;
        spi_ss_out      :   out std_logic_vector(3 downto 0);
        spi_en_out      :   out std_logic;
        spi_control_out :   out std_logic_vector(31 downto 0);
        spi_txd_out     :   out std_logic_vector(31 downto 0);
        spi_rxd_in      :   in  std_logic_vector(31 downto 0);
        spi_val_in      :   in  std_logic;
        rsp_sel_out     :   out std_logic_vector(mbus_w - 1 downto 0);
        rsp_data_in     :   in  std_logic_vector(rdbus_w - 1 downto 0);
        rsp_stat_in     :   in  std_logic_vector(rsbus_w - 1 downto 0);
        dbus_out        :   out std_logic_vector(dbus_w - 1 downto 0);
        abus_out        :   out std_logic_vector(abus_w - 1 downto 0);
        mbus_out        :   out std_logic_vector(mbus_w - 1 downto 0);
        cbus_out        :   out std_logic_vector(cbus_w - 1 downto 0)
    );
end entity central_control;

architecture parser of central_control is
    -- Debug variables
    signal debug_txd_mux    : std_logic; -- Mux for txd_out in debug mode
    signal debug_txd_buf    : std_logic_vector(7 downto 0); -- Buffer for txd_out in debug mode

    type state_type is (s_idle, s_fetch, s_receive, s_flip, s_parse_space, s_spi_parse_device,
                        s_spi_parse_data, s_spi_parse_control, s_spi_transmit, s_spi_listen,
                        s_bus_parse_device, s_bus_parse_head, s_bus_control_parse_body,
                        s_bus_write_parse_body, s_bus_write_parse_address,
                        s_bus_write_parse_data, s_bus_write_parse_mask,
                        s_bus_read_parse_body, s_bus_read_parse_address,
                        s_bus_misc_parse_body, s_bus_misc_parse_data, s_bus_transmit_1,
                        s_bus_transmit_2, s_bus_listen, s_respond_acknowledgement,
                        s_respond_exception, s_send);
    signal state        : state_type := s_idle;

    signal char_count   : unsigned(7 downto 0); -- Count of characters in a message
    signal aux_char_count : unsigned(2 downto 0); -- Count of characters in a segment, used to determine if a char is part of syntax

    signal cur_str      : std_logic_vector(31 downto 0); -- Current string being parsed

    signal response_data_buf    : std_logic_vector(31 downto 0); -- Buffer for response data
    signal response_data_attached : std_logic;
    signal response_err_buf     : std_logic_vector(31 downto 0); -- Buffer for response error
    constant response_err_attached : std_logic := '1'; -- For test purposes

    -- Buffers for bus commands
    signal bus_mod_buf  : std_logic_vector(mbus_w - 1 downto 0); -- Buffer for bus module
    signal bus_cmd_buf  : std_logic_vector(cbus_w - 1 downto 0); -- Buffer for bus command
    signal bus_addr_buf : std_logic_vector(abus_w - 1 downto 0); -- Buffer for bus address
    signal bus_data_buf : std_logic_vector(dbus_w - 1 downto 0); -- Buffer for bus data
    signal bus_mask_buf : std_logic_vector(dbus_w - 1 downto 0); -- Buffer for bus mask

    -- Buffers for spi commands
    signal spi_ss_buf       : std_logic_vector(3 downto 0); -- Buffer for spi slave select
    signal spi_control_buf  : std_logic_vector(31 downto 0); -- Buffer for spi control
    signal spi_data_buf     : std_logic_vector(31 downto 0); -- Buffer for spi data

    constant bsr_size   : integer := 64; -- Size of the bidirectional shift registers
    type bsr_type is array(0 to bsr_size - 1) of std_logic_vector(7 downto 0);

    -- Two shift registers used in the design.
    -- One flips the order of the characters in a message, and the other flips back.
    -- This is because the length of a message is unpredictable.
    -- By using two shift registers, the central control can always read the current character at address 0.
    signal bsr_i1_reg    : bsr_type; -- Shift registers
    signal bsr_i1_din    : std_logic_vector(7 downto 0); -- Data in
    signal bsr_i1_sl     : std_logic; -- Shift left, output
    signal bsr_i1_sr     : std_logic; -- Shift right, input
    signal bsr_i1_rst    : std_logic; -- Reset

    signal bsr_i2_reg    : bsr_type; -- Shift registers
    signal bsr_i2_din    : std_logic_vector(7 downto 0); -- Data in
    signal bsr_i2_sl     : std_logic; -- Shift left, output, 5 chars at a time
    signal bsr_i2_sr     : std_logic; -- Shift right, input
    signal bsr_i2_rst    : std_logic; -- Reset

    -- Output shift register stores the message to be sent
    signal bsr_o_reg     : bsr_type; -- Shift registers
    signal bsr_o_din     : bsr_type; -- Read all characters at once
    signal bsr_o_ren     : std_logic; -- Read enable
    signal bsr_o_sl      : std_logic; -- Shift left, output
    signal bsr_o_rst     : std_logic; -- Reset
begin
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                -- Reset to idle state
                state <= s_idle;
                rxen_out <= '0';
                txen_out <= '0';
                cbus_out <= (others => '0'); -- Clear the bus
                bsr_i1_sl <= '0';
                bsr_i2_sr <= '0';
                bsr_i1_sr <= '0';
                bsr_i2_sl <= '0';
                bsr_o_sl <= '0';
                bsr_o_ren <= '0';
                response_data_attached <= '0';
            else
                case state is
                    when s_idle =>
                        -- If a chatacter is available, fetch it
                        if rxemp_in = '0' then
                            rxen_out <= '1';
                            state <= s_fetch;
                        end if;
                        if is_debug = '1' then
                            debug_txd_mux <= '0';
                            txen_out <= '0';
                        end if;
                    when s_fetch =>
                        -- Wait for the fifo to return, while preparing the shift register
                        rxen_out <= '0';
                        bsr_i1_sr <= '1';
                        state <= s_receive;
                    when s_receive =>
                        -- Zero the chracter counter
                        char_count <= (others => '0');
                        aux_char_count <= (others => '0');
                        -- Receive the character with the shift register
                        bsr_i1_sr <= '0';
                        -- If the character is a terminator, start flipping the message
                        -- Also assert fifth and tenth characters are separators to prevent ambiguity
                        if rxd_in = u_TERM and bsr_i1_reg(4) = u_SEP and bsr_i1_reg(9) = u_SEP then
                            bsr_i1_sl <= '1';
                            bsr_i2_sr <= '1';
                            state <= s_flip;
                        else
                            state <= s_idle;
                        end if;
                        -- When in debug mode, respond with the received character
                        if is_debug = '1' then
                            debug_txd_buf <= rxd_in;
                            debug_txd_mux <= '1';
                            txen_out <= '1';
                        end if;
                    when s_flip =>
                        -- Count the length of the message
                        char_count <= char_count + x"01";
                        -- Count the position of characters in a segment
                        if aux_char_count = to_unsigned(4, 3) then
                            aux_char_count <= (others => '0');
                        else
                            aux_char_count <= aux_char_count + "001";
                        end if;
                        -- If the character is an initiator, AND the length of message is 5 * n + 1,
                        -- start parsing the message
                        if bsr_i1_reg(0) = u_INIT and aux_char_count = "000" then
                            bsr_i1_sl <= '0';
                            bsr_i2_sr <= '0';
                            bsr_i2_sl <= '1';
                            state <= s_parse_space;
                        elsif char_count = to_unsigned(bsr_size - 1, 8) then
                            -- If the message is too long, or the initiator is missing, throw an exception
                            response_err_buf <= x"4c4f4e47"; -- "LONG" for long message
                            state <= s_respond_exception;
                        end if;
                        if is_debug = '1' then
                            debug_txd_mux <= '0';
                            txen_out <= '0';
                        end if;
                    when s_parse_space =>
                        -- segment lies on bsr_i2_reg(1 to 5)
                        -- Assert that the end of current segment is a separator or a terminator, else throw an exception
                        if bsr_i2_reg(5) /= u_SEP then
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            case cur_str is
                                -- Parse space
                                when u_SPACE_SPI =>
                                    state <= s_spi_parse_device;
                                when u_SPACE_BUS =>
                                    state <= s_bus_parse_device;
                                when others =>
                                    response_err_buf <= x"53504153"; -- "SPAS" for space error
                                    state <= s_respond_exception;
                            end case;
                        end if;
                    when s_spi_parse_device =>
                        -- Parse the device
                        if bsr_i2_reg(5) /= u_SEP then
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            case cur_str is
                                when u_DEVICE_DAC1 =>
                                    spi_ss_buf <= std_logic_vector(to_unsigned(SPI_DAC1_ADDR, 4));
                                    state <= s_spi_parse_control;
                                when u_DEVICE_DAC2 =>
                                    spi_ss_buf <= std_logic_vector(to_unsigned(SPI_DAC2_ADDR, 4));
                                    state <= s_spi_parse_control;
                                when u_DEVICE_CLK1 =>
                                    spi_ss_buf <= std_logic_vector(to_unsigned(SPI_CLK1_ADDR, 4));
                                    state <= s_spi_parse_control;
                                when u_DEVICE_ADC1 =>
                                    spi_ss_buf <= std_logic_vector(to_unsigned(SPI_ADC1_ADDR, 4));
                                    state <= s_spi_parse_control;
                                when u_DEVICE_ADC2 =>
                                    spi_ss_buf <= std_logic_vector(to_unsigned(SPI_ADC2_ADDR, 4));
                                    state <= s_spi_parse_control;
                                when others =>
                                    response_err_buf <= x"44564345"; -- "DVCE" for device error
                                    state <= s_respond_exception;
                            end case;
                        end if;
                    when s_spi_parse_control =>
                        -- Parse the control
                        if bsr_i2_reg(5) /= u_SEP then
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            spi_control_buf <= cur_str(31 downto 0);
                            state <= s_spi_parse_data;
                        end if;
                    when s_spi_parse_data =>
                        -- Parse the data. No need to specify whether it is a reading or writing operation cuz spi is full duplex
                        if bsr_i2_reg(5) /= u_TERM then -- Assert end of message
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            spi_data_buf <= cur_str;
                            state <= s_spi_transmit;
                        end if;
                    when s_spi_transmit =>
                        bsr_i2_sl <= '0';
                        spi_en_out <= '1';
                        spi_ss_out <= spi_ss_buf;
                        spi_control_out <= spi_control_buf;
                        spi_txd_out <= spi_data_buf;
                        state <= s_spi_listen;
                    when s_spi_listen =>
                        spi_en_out <= '0';
                        if spi_val_in = '1' then
                            response_data_buf <= spi_rxd_in;
                            response_data_attached <= '1';
                            state <= s_respond_acknowledgement;
                        end if;
                    when s_bus_parse_device =>
                        -- Parse the device
                        if bsr_i2_reg(5) /= u_SEP then
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            case cur_str is
                                when u_DEVICE_ROUT =>
                                    bus_mod_buf <= BUS_ROUT_ADDR;
                                    state <= s_bus_parse_head;
                                when u_DEVICE_TRIG =>
                                    bus_mod_buf <= BUS_TRIG_ADDR;
                                    state <= s_bus_parse_head;
                                when u_DEVICE_ACCM =>
                                    bus_mod_buf <= BUS_ACCM_ADDR;
                                    state <= s_bus_parse_head;
                                when u_DEVICE_SCLR =>
                                    bus_mod_buf <= BUS_SCLR_ADDR;
                                    state <= s_bus_parse_head;
                                when u_DEVICE_MMWR =>
                                    bus_mod_buf <= BUS_MMWR_ADDR;
                                    state <= s_bus_parse_head;
                                when u_DEVICE_PIDC =>
                                    bus_mod_buf <= BUS_PIDC_ADDR;
                                    state <= s_bus_parse_head;
                                when others =>
                                    response_err_buf <= x"44564345"; -- "DVCE" for device error
                                    state <= s_respond_exception;
                            end case;
                        end if;
                    when s_bus_parse_head =>
                        -- Parse the specific command. Constants defined in bus_protocol
                        if bsr_i2_reg(5) /= u_SEP then
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            case cur_str is
                                when u_COMMAND_CTRL =>
                                    bus_cmd_buf(cbus_w - 1 downto cbus_w - 2) <= CONTROL_HEAD;
                                    state <= s_bus_control_parse_body;
                                when u_COMMAND_READ =>
                                    bus_cmd_buf(cbus_w - 1 downto cbus_w - 2) <= READ_HEAD;
                                    bus_cmd_buf(cbus_w - 3 downto 0) <= (others => '0');
                                    state <= s_bus_read_parse_body;
                                when u_COMMAND_WRTE =>
                                    bus_cmd_buf(cbus_w - 1 downto cbus_w - 2) <= WRITE_HEAD;
                                    bus_cmd_buf(cbus_w - 3 downto 0) <= (others => '0');
                                    state <= s_bus_write_parse_body;
                                when u_COMMAND_MISC =>
                                    bus_cmd_buf(cbus_w - 1 downto cbus_w - 2) <= MISC_HEAD;
                                    bus_cmd_buf(cbus_w - 3 downto 0) <= (others => '0');
                                    state <= s_bus_misc_parse_body;
                                when others =>
                                    response_err_buf <= x"48454144"; -- "HEAD" for head error
                                    state <= s_respond_exception;
                            end case;
                        end if;
                    when s_bus_control_parse_body =>
                        -- Parse the specific action. Constants defined in bus_protocol
                        if bsr_i2_reg(5) /= u_TERM then -- Assert end of message
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            case cur_str is
                                when u_KEYWORD_SETC =>
                                    bus_cmd_buf(cbus_w - 3 downto 0) <= SET_CORE;
                                    state <= s_bus_transmit_1;
                                when u_KEYWORD_RSTC =>
                                    bus_cmd_buf(cbus_w - 3 downto 0) <= RST_CORE;
                                    state <= s_bus_transmit_1;
                                when u_KEYWORD_SETR =>
                                    bus_cmd_buf(cbus_w - 3 downto 0) <= SET_RAM;
                                    state <= s_bus_transmit_1;
                                when u_KEYWORD_RSTR =>
                                    bus_cmd_buf(cbus_w - 3 downto 0) <= RST_RAM;
                                    state <= s_bus_transmit_1;
                                when others =>
                                    response_err_buf <= x"424f4459"; -- "BODY" for body error
                                    state <= s_respond_exception;
                            end case;
                        end if;
                    when s_bus_write_parse_body =>
                        if bsr_i2_reg(5) /= u_SEP and bsr_i2_reg(5) /= u_TERM then
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            case cur_str is
                                when u_KEYWORD_ADDR =>
                                    state <= s_bus_write_parse_address;
                                when u_KEYWORD_DATA =>
                                    state <= s_bus_write_parse_data;
                                when u_KEYWORD_MASK =>
                                    bus_cmd_buf(cbus_w - 3) <= '1'; -- Could cause problems in the future, assuming third MSB indicates whether a mask is added
                                    state <= s_bus_write_parse_mask;
                                when u_KEYWORD_HOLD =>
                                    bus_cmd_buf(0) <= '1'; -- Could cause problems in the future, assuming LSB indicates hold
                                    if bsr_i2_reg(5) = u_TERM then
                                        state <= s_bus_transmit_1;
                                    end if;
                                when others =>
                                    response_err_buf <= x"424f4459"; -- "BODY" for body error
                                    state <= s_respond_exception;
                            end case;
                        end if;
                    when s_bus_write_parse_address =>
                        if bsr_i2_reg(5) /= u_SEP and bsr_i2_reg(5) /= u_TERM then
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            bus_addr_buf <= cur_str(abus_w - 1 downto 0);
                            if bsr_i2_reg(5) = u_TERM then
                                state <= s_bus_transmit_1;
                            else
                                state <= s_bus_write_parse_body;
                            end if;
                        end if;
                    when s_bus_write_parse_data =>
                        if bsr_i2_reg(5) /= u_SEP and bsr_i2_reg(5) /= u_TERM then
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            bus_data_buf <= cur_str(dbus_w - 1 downto 0);
                            if bsr_i2_reg(5) = u_TERM then
                                state <= s_bus_transmit_1;
                            else
                                state <= s_bus_write_parse_body;
                            end if;
                        end if;
                    when s_bus_write_parse_mask =>
                        if bsr_i2_reg(5) /= u_SEP and bsr_i2_reg(5) /= u_TERM then
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            bus_mask_buf <= cur_str(dbus_w - 1 downto 0);
                            if bsr_i2_reg(5) = u_TERM then
                                state <= s_bus_transmit_1;
                            else
                                state <= s_bus_write_parse_body;
                            end if;
                        end if;
                    when s_bus_read_parse_body =>
                        if bsr_i2_reg(5) /= u_SEP then
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            case cur_str is
                                when u_KEYWORD_ADDR =>
                                    state <= s_bus_read_parse_address;
                                when others =>
                                    response_err_buf <= x"424f4459"; -- "BODY" for body error
                                    state <= s_respond_exception;
                            end case;
                        end if;
                    when s_bus_read_parse_address =>
                        if bsr_i2_reg(5) /= u_SEP and bsr_i2_reg(5) /= u_TERM then
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            bus_addr_buf <= cur_str(abus_w - 1 downto 0);
                            if bsr_i2_reg(5) = u_TERM then
                                state <= s_bus_transmit_1;
                            else
                                state <= s_bus_read_parse_body;
                            end if;
                        end if;
                    when s_bus_misc_parse_body =>
                        if bsr_i2_reg(5) /= u_SEP then
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            case cur_str is
                                when u_KEYWORD_DATA =>
                                    state <= s_bus_misc_parse_data;
                                when others =>
                                    response_err_buf <= x"424f4459"; -- "BODY" for body error
                                    state <= s_respond_exception;
                            end case;
                        end if;
                    when s_bus_misc_parse_data =>
                        if bsr_i2_reg(5) /= u_TERM then -- Assert end of message
                            response_err_buf <= x"534e5458"; -- "SNTX" for syntax error
                            state <= s_respond_exception;
                        else
                            bus_data_buf <= cur_str(dbus_w - 1 downto 0);
                            state <= s_bus_transmit_1;
                        end if;
                    -- Sending bus commands in multiple steps. Refer to bus_protocol for details.
                    when s_bus_transmit_1 =>
                        bsr_i2_sl <= '0';
                        rsp_sel_out <= bus_mod_buf;
                        mbus_out <= bus_mod_buf;
                        cbus_out <= bus_cmd_buf;
                        abus_out <= bus_addr_buf;
                        dbus_out <= bus_data_buf;
                        if bus_cmd_buf(cbus_w - 1 downto cbus_w - 3) = WRITE_HEAD & '1' then -- Could cause problems in the future, assuming third MSB indicates whether a mask is added
                            state <= s_bus_transmit_2;
                        else
                            state <= s_bus_listen;
                        end if;
                    when s_bus_transmit_2 =>
                        cbus_out <= (others => '0');
                        dbus_out <= bus_mask_buf;
                        state <= s_bus_listen;
                    when s_bus_listen =>
                        cbus_out <= (others => '0');
                        case rsp_stat_in is
                            when ROGER =>
                                if bus_cmd_buf(cbus_w - 1 downto cbus_w - 2) = READ_HEAD then
                                    response_data_buf <= rsp_data_in;
                                    response_data_attached <= '1';
                                end if;
                                state <= s_respond_acknowledgement;
                            when ERROR =>
                                response_err_buf <= rsp_data_in;
                                state <= s_respond_exception;
                            when others =>
                        end case;
                    when s_respond_acknowledgement =>
                        -- Load an acknowledgement message
                        bsr_i2_sl <= '0';
                        bsr_o_ren <= '1';
                        bsr_o_din(0) <= u_INIT;
                        bsr_o_din(1) <= u_RESPONSE_ACKN(31 downto 24);
                        bsr_o_din(2) <= u_RESPONSE_ACKN(23 downto 16);
                        bsr_o_din(3) <= u_RESPONSE_ACKN(15 downto 8);
                        bsr_o_din(4) <= u_RESPONSE_ACKN(7 downto 0);
                        if response_data_attached = '1' then
                            bsr_o_din(5) <= u_SEP;
                            bsr_o_din(6) <= response_data_buf(31 downto 24);
                            bsr_o_din(7) <= response_data_buf(23 downto 16);
                            bsr_o_din(8) <= response_data_buf(15 downto 8);
                            bsr_o_din(9) <= response_data_buf(7 downto 0);
                            bsr_o_din(10) <= u_TERM;
                        else
                            bsr_o_din(5) <= u_TERM;
                        end if;
                        response_data_attached <= '0';
                        state <= s_send;
                    when s_respond_exception =>
                        -- Load an exception message
                        bsr_i2_sl <= '0';
                        bsr_o_ren <= '1';
                        bsr_o_din(0) <= u_INIT;
                        bsr_o_din(1) <= u_RESPONSE_ERR(31 downto 24);
                        bsr_o_din(2) <= u_RESPONSE_ERR(23 downto 16);
                        bsr_o_din(3) <= u_RESPONSE_ERR(15 downto 8);
                        bsr_o_din(4) <= u_RESPONSE_ERR(7 downto 0);
                        if response_err_attached = '1' then
                            bsr_o_din(5) <= u_SEP;
                            bsr_o_din(6) <= response_err_buf(31 downto 24);
                            bsr_o_din(7) <= response_err_buf(23 downto 16);
                            bsr_o_din(8) <= response_err_buf(15 downto 8);
                            bsr_o_din(9) <= response_err_buf(7 downto 0);
                            bsr_o_din(10) <= u_TERM;
                        else
                            bsr_o_din(5) <= u_TERM;
                        end if;
                        state <= s_send;
                    when s_send =>
                        -- Send the message loaded in the output shift register
                        bsr_o_ren <= '0';
                        if bsr_o_reg(0) = u_TERM then
                            txen_out <= '0';
                            bsr_o_sl <= '0';
                            state <= s_idle;
                        else
                            bsr_o_sl <= '1';
                            txen_out <= '1';
                        end if;
                end case;
            end if;
        end if;
    end process;

    -- String matching
    cur_str <= bsr_i2_reg(1) & bsr_i2_reg(2) & bsr_i2_reg(3) & bsr_i2_reg(4);

    -- Input shift register 1
    process(clk)
    begin
        if rising_edge(clk) then
            if bsr_i1_rst = '1' then
                bsr_i1_reg <= (others => (others => '0'));
            else
                if bsr_i1_sr = '1' then
                    for i in bsr_size - 1 downto 1 loop
                        bsr_i1_reg(i) <= bsr_i1_reg(i - 1);
                    end loop;
                    bsr_i1_reg(0) <= bsr_i1_din;
                elsif bsr_i1_sl = '1' then
                    for i in 1 to bsr_size - 1 loop
                        bsr_i1_reg(i - 1) <= bsr_i1_reg(i);
                    end loop;
                end if;
            end if;
        end if;
    end process;
    bsr_i1_din <= rxd_in;
    bsr_i1_rst <= rst;

    -- Input shift register 2
    process(clk)
    begin
        if rising_edge(clk) then
            if bsr_i2_rst = '1' then
                bsr_i2_reg <= (others => (others => '0'));
            else
                if bsr_i2_sr = '1' then
                    for i in bsr_size - 1 downto 1 loop
                        bsr_i2_reg(i) <= bsr_i2_reg(i - 1);
                    end loop;
                    bsr_i2_reg(0) <= bsr_i2_din;
                elsif bsr_i2_sl = '1' then
                    for i in 5 to bsr_size - 1 loop 
                        bsr_i2_reg(i - 5) <= bsr_i2_reg(i); -- read 5 characters at a time
                    end loop;
                end if;
            end if;
        end if;
    end process;
    bsr_i2_din <= bsr_i1_reg(0);
    bsr_i2_rst <= rst;
    
    -- Output shift register
    process(clk)
    begin
        if rising_edge(clk) then
            if bsr_o_rst = '1' then
                bsr_o_reg <= (others => (others => '0'));
            else
                if bsr_o_ren = '1' then
                    bsr_o_reg <= bsr_o_din;
                elsif bsr_o_sl = '1' then
                    for i in 1 to bsr_size - 1 loop
                        bsr_o_reg(i - 1) <= bsr_o_reg(i);
                    end loop;
                end if;
            end if;
        end if;
    end process;
    txd_gen : if is_debug = '0' generate
        txd_out <= bsr_o_reg(0);
    end generate txd_gen;
    debug_txd_gen : if is_debug = '1' generate
        txd_out <= bsr_o_reg(0) when debug_txd_mux = '0' else debug_txd_buf;
    end generate debug_txd_gen;
    bsr_o_rst <= rst;
end parser;

-- This is a simple architecture that repeats any byte received.
-- It was used for testing purposes.
/*
architecture repeater of central_control is
    type state_type is (idle, hold, receive, transmit, error);
    signal state    :   state_type := idle;
    signal byte     :   std_logic_vector(7 downto 0);

    signal cnt      :   unsigned(2 downto 0) := (others => '0');
begin
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                rxen_out <= '0';
                txen_out <= '0';
                byte <= (others => '0');
                txd_out <= (others => '0');
                state <= idle;
            else
                case state is
                    when idle =>
                        txen_out <= '0';
                        if rxemp_in = '0' then
                            rxen_out <= '1';
                            state <= hold;
                        end if;
                    when hold =>
                        rxen_out <= '0';
                        state <= receive;
                    when receive =>
                        byte <= rxd_in;
                        if txful_in = '0' then
                            state <= transmit;
                        else
                            state <= error;
                        end if;
                    when transmit =>
                        txen_out <= '1';
                        txd_out <= byte;
                        state <= idle;
                    when error =>
                        -- Do nothing
                end case;
            end if;
        end if;
    end process;
    
    process(clk)
    begin
        if rising_edge(clk) then
            if state = transmit then
                cnt <= cnt + "001";
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            case cnt is
                when "000" =>
                    dbus_out(7 downto 0) <= byte;
                when "001" =>
                    dbus_out(15 downto 8) <= byte;
                when "010" =>
                    dbus_out(23 downto 16) <= byte;
                when "011" =>
                    dbus_out(31 downto 24) <= byte;
                when "100" =>
                    abus_out <= byte(4 downto 0);
                when "101" =>
                    mbus_out <= byte(4 downto 0);
                when "110" =>
                    cbus_out <= byte(4 downto 0);
                when "111" =>
                    rsp_sel_out <= byte(4 downto 0);
                when others =>
            end case;
        end if;
    end process;
end architecture repeater;
*/