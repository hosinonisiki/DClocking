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

    type init_lut_type is array(natural range <>) of std_logic_vector(67 downto 0);
    constant init_lut_size : natural := 161; -- Blank for now, max 255
    constant init_lut : init_lut_type(0 to init_lut_size - 1) := (
        -- trx_ss_out(3 downto 0) | trx_control_out(31 downto 0) | trx_dout(31 downto 0)
        -- FL9627
        x"0_0000_1717_00003C_00",
        x"0_0000_1717_000018_00",
        x"0_0000_1717_000503_00",
        x"0_0000_1717_001441_00",
        x"0_0000_1717_001705_00",
        x"0_0000_1717_00FF01_00",
        x"1_0000_1717_00003C_00",
        x"1_0000_1717_000018_00",
        x"1_0000_1717_000503_00",
        x"1_0000_1717_001441_00",
        x"1_0000_1717_001705_00",
        x"1_0000_1717_00FF01_00",
        -- AD9528, write to non-existing address to simulate delay
        x"A_0000_1717_000081_00",
        x"F_0000_1F1F_00000000",
        x"A_0000_1717_000000_00",
        x"A_0000_1717_000100_00",
        x"A_0000_1717_000F01_00",
        x"A_0000_1717_010001_00",
        x"A_0000_1717_010100_00",
        x"A_0000_1717_010201_00",
        x"A_0000_1717_010300_00",
        x"A_0000_1717_01040A_00",
        x"A_0000_1717_010500_00",
        x"A_0000_1717_01060A_00",
        x"A_0000_1717_010723_00",
        x"A_0000_1717_010829_00",
        x"A_0000_1717_010914_00",
        x"A_0000_1717_010A06_00",
        x"A_0000_1717_02000A_00",
        x"A_0000_1717_02010A_00",
        x"A_0000_1717_020203_00",
        x"A_0000_1717_020300_00",
        x"A_0000_1717_020404_00",
        x"A_0000_1717_02053A_00",
        x"A_0000_1717_020600_00",
        x"A_0000_1717_020701_00",
        x"A_0000_1717_020809_00",
        x"A_0000_1717_030000_00",
        x"A_0000_1717_030100_00",
        x"A_0000_1717_0302FF_00",
        x"A_0000_1717_030600_00",
        x"A_0000_1717_030700_00",
        x"A_0000_1717_030800_00",
        x"A_0000_1717_030900_00",
        x"A_0000_1717_030A00_00",
        x"A_0000_1717_030B03_00",
        x"A_0000_1717_030C00_00",
        x"A_0000_1717_030D00_00",
        x"A_0000_1717_030E00_00",
        x"A_0000_1717_030F00_00",
        x"A_0000_1717_031000_00",
        x"A_0000_1717_0311FF_00",
        x"A_0000_1717_031200_00",
        x"A_0000_1717_031300_00",
        x"A_0000_1717_031404_00",
        x"A_0000_1717_031500_00",
        x"A_0000_1717_031600_00",
        x"A_0000_1717_031703_00",
        x"A_0000_1717_031800_00",
        x"A_0000_1717_031900_00",
        x"A_0000_1717_031AFF_00",
        x"A_0000_1717_031B00_00",
        x"A_0000_1717_031C00_00",
        x"A_0000_1717_031DFF_00",
        x"A_0000_1717_031E00_00",
        x"A_0000_1717_031F00_00",
        x"A_0000_1717_032004_00",
        x"A_0000_1717_032700_00",
        x"A_0000_1717_032800_00",
        x"A_0000_1717_032903_00",
        x"A_0000_1717_032A00_00",
        x"A_0000_1717_032B00_00",
        x"A_0000_1717_032C00_00",
        x"A_0000_1717_032D00_00",
        x"A_0000_1717_032E00_00",
        x"A_0000_1717_040040_00",
        x"A_0000_1717_040100_00",
        x"A_0000_1717_040218_00",
        x"A_0000_1717_040396_00",
        x"A_0000_1717_040404_00",
        x"A_0000_1717_050010_00",
        x"A_0000_1717_050100_00",
        x"A_0000_1717_050200_00",
        x"A_0000_1717_0503FF_00",
        x"A_0000_1717_0504FF_00",
        x"A_0000_1717_000F01_00",
        x"A_0000_1717_040397_00",
        x"A_0000_1717_000F01_00",
        x"F_0000_1F1F_00000000",
        x"A_0000_1717_020301_00",
        x"A_0000_1717_000F01_00",
        x"A_0000_1717_020300_00",
        x"A_0000_1717_000F01_00",
        x"A_0000_1717_032A01_00",
        x"A_0000_1717_000F01_00",
        x"A_0000_1717_032A00_00",
        x"A_0000_1717_000F01_00",
        -- AD9680
        x"8_0000_1717_000081_00",
        x"F_0000_1F1F_00000000",
        x"8_0000_1717_057115_00",
        x"8_0000_1717_05BD1F_00",
        x"8_0000_1717_058F2F_00",
        x"8_0000_1717_05902F_00",
        x"8_0000_1717_057088_00",
        x"8_0000_1717_056E00_00",
        x"8_0000_1717_058B83_00",
        x"8_0000_1717_01200A_00",
        x"8_0000_1717_057114_00",
        --AD9152
        x"9_0000_1717_000081_00",
        x"F_0000_1F1F_00000000",
        x"9_0000_1717_000000_00",
        x"9_0000_1717_001100_00",
        x"9_0000_1717_008000_00",
        x"9_0000_1717_008100_00",
        x"9_0000_1717_011200_00",
        x"9_0000_1717_011000_00",
        x"9_0000_1717_020000_00",
        x"9_0000_1717_020100_00",
        x"9_0000_1717_023028_00",
        x"9_0000_1717_031220_00",
        x"9_0000_1717_030000_00",
        x"9_0000_1717_045000_00",
        x"9_0000_1717_045100_00",
        x"9_0000_1717_045204_00",
        x"9_0000_1717_045383_00",
        x"9_0000_1717_045400_00",
        x"9_0000_1717_04551F_00",
        x"9_0000_1717_045601_00",
        x"9_0000_1717_04570F_00",
        x"9_0000_1717_04582F_00",
        x"9_0000_1717_045920_00",
        x"9_0000_1717_045A80_00",
        x"9_0000_1717_045D49_00",
        x"9_0000_1717_047801_00",
        x"9_0000_1717_046C0F_00",
        x"9_0000_1717_047601_00",
        x"9_0000_1717_047D0F_00",
        x"9_0000_1717_02A608_00",
        x"9_0000_1717_0248AA_00",
        x"9_0000_1717_02AAB7_00",
        x"9_0000_1717_02AB87_00",
        x"9_0000_1717_02A701_00",
        x"9_0000_1717_031401_00",
        x"9_0000_1717_023028_00",
        x"9_0000_1717_020600_00",
        x"9_0000_1717_020601_00",
        x"9_0000_1717_028904_00",
        x"9_0000_1717_028001_00",
        x"9_0000_1717_028005_00",
        x"F_0000_1F1F_00000000",
        x"9_0000_1717_026862_00",
        x"9_0000_1717_030808_00",
        x"9_0000_1717_030913_00",
        x"9_0000_1717_030101_00",
        x"9_0000_1717_030400_00",
        x"9_0000_1717_03060A_00",
        x"9_0000_1717_003A01_00",
        x"9_0000_1717_003A81_00",
        x"9_0000_1717_003AC1_00",
        x"9_0000_1717_030001_00",
        x"9_0000_1717_00E730_00"
    );
    signal init_lut_idx : unsigned(7 downto 0) := (others => '0');
    signal init_done : std_logic := '0';

    constant query_interval : unsigned(31 downto 0) := to_unsigned(clk_freq / 10, 32); -- Query every 100ms
    signal query_cnt : unsigned(31 downto 0) := (others => '0');
    type query_lut_type is array(natural range <>) of std_logic_vector(131 downto 0);
    constant query_lut_size : natural := 3; -- Blank for now, max 4, same as the width of query_result_out
    constant query_lut : query_lut_type(0 to query_lut_size - 1) := (
        -- trx_ss_out(3 downto 0) | trx_control_out(31 downto 0) | trx_dout(31 downto 0) | query_result_mask(31 downto 0) | expected_query_result(31 downto 0)
        x"A_0000_0F17_8508_0000_0000_00F0_0000_00E0",
        x"8_0000_0F17_856F_0000_0000_00FF_0000_0080",
        x"9_0000_0F17_8281_0000_0000_00FF_0000_0003"
    );
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
            if state = s_query and query_lut_idx = to_unsigned(query_lut_size, 8) then
                query_lut_idx <= (others => '0');
            elsif state = s_query_listen and trx_dval_in = '1' then
                query_lut_idx <= query_lut_idx + x"01";
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if query_start = '0' then
                query_cnt <= query_cnt + x"00000001";
            else
                query_cnt <= (others => '0');
            end if;
        end if;
    end process;

    process(clk) 
    begin
        if rising_edge(clk) then
            if query_done = '1' then
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
            if trx_spi_en = '1' then
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
            if state = s_forward_listen and trx_dval_in = '1' then
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
            if state = s_query_listen and trx_dval_in = '1' then
                if (trx_din and query_lut(to_integer(query_lut_idx))(63 downto 32)) = query_lut(to_integer(query_lut_idx))(31 downto 0) then
                    query_result_out(to_integer(query_lut_idx)) <= '1';
                else
                    query_result_out(to_integer(query_lut_idx)) <= '0';
                end if;
            end if;
        end if;
    end process;
end behavioral;