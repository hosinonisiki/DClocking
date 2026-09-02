-- ///////////////Documentation////////////////////
-- This design is for the needs of setting up certain
-- chip registers on powering up and for regularly
-- querying certain registers. It is inserted between
-- the central control module and spi_trx module from
-- previous design. It intercepts SPI requests from central
-- control, coordinates them with powering up and
-- periodically querying SPI transmissions, and handles
-- communications with the spi_trx, replacing the
-- former direct connection between central control and spi_trx.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;
use work.KU060_custom_config.all;

entity spi_task_control is
    port(
        clk                 :   in  std_logic;
        rst                 :   in  std_logic;
        cmd_spi_en_in       :   in  std_logic;
        cmd_ss_in           :   in  std_logic_vector(3 downto 0);
        cmd_control_in      :   in  std_logic_vector(31 downto 0);
        cmd_din             :   in  std_logic_vector(31 downto 0);
        cmd_dout            :   out std_logic_vector(31 downto 0) := (others => '0');
        cmd_dval_out        :   out std_logic := '0';
        cmd_idle_out        :   out std_logic := '0';
        trx_spi_en_out      :   out std_logic := '0';
        trx_ss_out          :   out std_logic_vector(3 downto 0) := (others => '0');
        trx_control_out     :   out std_logic_vector(31 downto 0) := (others => '0');
        trx_dout            :   out std_logic_vector(31 downto 0) := (others => '0');
        trx_din             :   in std_logic_vector(31 downto 0);
        trx_dval_in         :   in  std_logic;
        trx_idle_in         :   in  std_logic;
        query_result_out    :   out std_logic_vector(0 to 3) := (others => '0')
    );
end spi_task_control;

architecture behavioral of spi_task_control is
    type state_type is (s_powerup_hold, s_init, s_init_transmit, s_init_listen, s_idle_pre, s_idle, s_query, s_query_transmit, s_query_listen, s_forward_transmit, s_forward_listen);

    signal state : state_type := s_powerup_hold;
    constant powerup_hold_time : unsigned(31 downto 0) := to_unsigned(clk_freq * 5, 32); -- Hold for 5s on power up
    signal powerup_hold_cnt : unsigned(31 downto 0) := (others => '0');
    signal powerup_hold_done : std_logic := '0';

    signal init_lut_idx : unsigned(7 downto 0) := (others => '0');
    signal init_done : std_logic := '0';

    constant query_interval : unsigned(31 downto 0) := to_unsigned(clk_freq / 10, 32); -- Query every 100ms
    signal query_cnt : unsigned(31 downto 0) := (others => '0');

    signal query_lut_idx : unsigned(7 downto 0) := (others => '0');
    signal query_start : std_logic := '0';
    signal query_done : std_logic := '0';

    signal cmd_ss_buf : std_logic_vector(3 downto 0) := (others => '0');
    signal cmd_control_buf : std_logic_vector(31 downto 0) := (others => '0');
    signal cmd_din_buf : std_logic_vector(31 downto 0) := (others => '0');

    signal trx_spi_en : std_logic := '0';
begin
    process(clk)
    begin
        if rising_edge(clk) then
            case state is
                when s_powerup_hold =>
                    if powerup_hold_done = '1' then
                        state <= s_init;
                    end if;
                when s_init =>
                    if init_lut_idx = to_unsigned(init_lut_size, 8) then
                        state <= s_idle;
                        init_done <= '1';
                    else
                        state <= s_init_transmit;
                    end if;
                when s_init_transmit =>
                    if trx_idle_in = '1' then
                        state <= s_init_listen;
                    end if;
                when s_init_listen =>
                    if trx_dval_in = '1' then
                        state <= s_init;
                    end if;
                when others =>
                    if rst = '1' then
                        state <= s_idle_pre;
                    else
                        case state is
                            when s_idle_pre =>
                                state <= s_idle;
                            when s_idle =>
                                if cmd_spi_en_in = '1' then
                                    state <= s_forward_transmit;
                                elsif query_start = '1' then
                                    state <= s_query;
                                end if;
                            when s_query =>
                                if query_lut_idx = to_unsigned(query_lut_size, 8) then
                                    state <= s_idle_pre;
                                else
                                    state <= s_query_transmit;
                                end if;
                            when s_query_transmit =>
                                if trx_idle_in = '1' then
                                    state <= s_query_listen;
                                end if;
                            when s_query_listen =>
                                if trx_dval_in = '1' then
                                    state <= s_query;
                                end if;
                            when s_forward_transmit =>
                                if trx_idle_in = '1' then
                                    state <= s_forward_listen;
                                end if;
                            when s_forward_listen =>
                                if trx_dval_in = '1' then
                                    state <= s_idle_pre;
                                end if;
                            when others =>
                                state <= s_idle_pre;
                        end case;
                    end if;
            end case;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            powerup_hold_cnt <= powerup_hold_cnt + x"00000001";
        end if;
    end process;
    powerup_hold_done <= '1' when powerup_hold_cnt = powerup_hold_time else '0';

    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_init_listen and trx_dval_in = '1' then
                init_lut_idx <= init_lut_idx + x"01";
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                query_lut_idx <= (others => '0');
            elsif state = s_query and query_lut_idx = to_unsigned(query_lut_size, 8) then
                query_lut_idx <= (others => '0');
            elsif state = s_query_listen and trx_dval_in = '1' then
                query_lut_idx <= query_lut_idx + x"01";
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                query_cnt <= (others => '0');
            elsif query_start = '0' then
                query_cnt <= query_cnt + x"00000001";
            else
                query_cnt <= (others => '0');
            end if;
        end if;
    end process;

    process(clk) 
    begin
        if rising_edge(clk) then
            if rst = '1' then
                query_start <= '0';
            elsif query_done = '1' then
                query_start <= '0';
            elsif query_cnt = query_interval then
                query_start <= '1';
            end if;
        end if;
    end process;
    query_done <= '1' when state = s_query and query_lut_idx = to_unsigned(query_lut_size, 8) else '0';

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                trx_spi_en <= '0';
            elsif trx_spi_en = '1' then
                trx_spi_en <= '0';
            elsif trx_idle_in = '1' then
                case state is
                    when s_init_transmit =>
                        trx_spi_en <= '1';
                        trx_ss_out <= init_lut(to_integer(init_lut_idx))(67 downto 64);
                        trx_control_out <= init_lut(to_integer(init_lut_idx))(63 downto 32);
                        trx_dout <= init_lut(to_integer(init_lut_idx))(31 downto 0);
                    when s_query_transmit =>
                        trx_spi_en <= '1';
                        trx_ss_out <= query_lut(to_integer(query_lut_idx))(131 downto 128);
                        trx_control_out <= query_lut(to_integer(query_lut_idx))(127 downto 96);
                        trx_dout <= query_lut(to_integer(query_lut_idx))(95 downto 64);
                    when s_forward_transmit =>
                        trx_spi_en <= '1';
                        trx_ss_out <= cmd_ss_buf;
                        trx_control_out <= cmd_control_buf;
                        trx_dout <= cmd_din_buf;
                    when others =>
                end case;
            end if;
        end if;
    end process;
    trx_spi_en_out <= trx_spi_en;

    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_idle and cmd_spi_en_in = '1' then
                cmd_ss_buf <= cmd_ss_in;
                cmd_control_buf <= cmd_control_in;
                cmd_din_buf <= cmd_din;
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                cmd_dout <= (others => '0');
                cmd_dval_out <= '0';
            elsif state = s_forward_listen and trx_dval_in = '1' then
                cmd_dout <= trx_din;
                cmd_dval_out <= '1';
            else
                cmd_dval_out <= '0';
            end if;
        end if;
    end process;
    cmd_idle_out <= '1' when state = s_idle or state = s_idle_pre else '0';

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                query_result_out <= (others => '0');
            elsif state = s_query_listen and trx_dval_in = '1' then
                if (trx_din and query_lut(to_integer(query_lut_idx))(63 downto 32)) = query_lut(to_integer(query_lut_idx))(31 downto 0) then
                    query_result_out(to_integer(query_lut_idx)) <= '1';
                else
                    query_result_out(to_integer(query_lut_idx)) <= '0';
                end if;
            end if;
        end if;
    end process;
end behavioral;
