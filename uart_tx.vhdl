-- ///////////////Documentation////////////////////
-- Simple uart transmitter.

-- Uart/USB conversion done by CP2102-GM

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity uart_tx is
    generic(
        -- clk_freq and baudrate defined in mypak
        data_bits       :   integer := 8;
        stop_bits       :   integer := 1;
        parity_type     :   string  := "even" -- "none", "odd", "even", "mark", "space"
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        txd_out         :   out std_logic := '1';
        din             :   in  std_logic_vector(data_bits - 1 downto 0) := (others => '0');
        dval_in         :   in  std_logic; -- '1' indicates data incoming
        den_out         :   out std_logic := '0'; -- set '1' to retrieve data
        idle_out        :   out std_logic := '0'
    );
end entity uart_tx;

architecture behavioral of uart_tx is
    constant data_bits_u        :   unsigned(3 downto 0) := to_unsigned(data_bits, 4);
    constant stop_bits_u        :   unsigned(3 downto 0) := to_unsigned(stop_bits, 4);
    constant bit_length         :   unsigned(15 downto 0) := to_unsigned(clk_freq / baudrate, 16); -- clock cycles per bit

    type state_type is (s_idle, s_init_1, s_init_2, s_data, s_parity, s_stop, s_wait);
    signal state                :   state_type := s_idle;
    signal last_state           :   state_type := s_idle;

    signal cycle_cnt            :   unsigned(15 downto 0); -- min baudrate 4800
    signal bit_cnt              :   unsigned(3 downto 0);

    signal data                 :   std_logic_vector(data_bits - 1 downto 0);
    signal parity               :   std_logic;
    signal bit_ready            :   std_logic;
    signal data_final_dgt       :   std_logic;
    signal stop_final_dgt       :   std_logic;
begin
    
    process(clk, rst)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                state <= s_idle;
            else
                case state is
                    when s_idle => 
                        if dval_in = '1' then
                            state <= s_init_1;
                        end if;
                    when s_init_1 =>
                        state <= s_init_2;
                    when s_init_2 =>
                        state <= s_data;
                    when s_data =>
                        if bit_ready = '1' and data_final_dgt = '1' then
                            if parity_type = "none" then
                                state <= s_stop;
                            else
                                state <= s_parity;
                            end if;
                        end if;
                    when s_parity =>
                        if bit_ready = '1' then
                            state <= s_stop;
                        end if;
                    when s_stop =>
                        if bit_ready = '1' and stop_final_dgt = '1' then
                            state <= s_wait;
                        end if;
                    when s_wait =>
                        if bit_ready = '1' then
                            state <= s_idle;
                        end if;
                end case;
            end if;
            last_state <= state;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_idle or bit_ready = '1' then
                cycle_cnt <= x"0000";
            else
                cycle_cnt <= cycle_cnt + x"0001";
            end if;
        end if;
    end process;
    
    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_idle or (state = s_stop and last_state /= s_stop) then
                bit_cnt <= x"0";
            elsif bit_ready = '1' then
                bit_cnt <= bit_cnt + x"1";
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_data then
                if bit_ready = '1' then
                    data <= '0' & data(data_bits - 1 downto 1);
                end if;
            else
                data <= din;
            end if;
        end if;
    end process;

    parity <= xor data;

    process(clk)
    begin
        if rising_edge(clk) then
            case state is
                when s_init_2 =>
                    txd_out <= '0';
                when s_data =>
                    if bit_ready = '1' then
                        txd_out <= data(0);
                    end if;
                when s_parity =>
                    if bit_ready = '1' then
                        case parity_type is
                            when "even" =>
                                txd_out <= parity;
                            when "odd" =>
                                txd_out <= not parity;
                            when "mark" =>
                                txd_out <= '1';
                            when "space" =>
                                txd_out <= '0';
                            when others =>
                        end case;
                    end if;
                when s_stop =>
                    if bit_ready = '1' then
                        txd_out <= '1';
                    end if;
                when others =>
                    txd_out <= '1';
            end case;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_idle and dval_in = '1' then
                den_out <= '1';
            else
                den_out <= '0';
            end if;
        end if;
    end process;

    idle_out <= '1' when state = s_idle and rst = '0' else '0';

    bit_ready <= '1' when cycle_cnt = bit_length + x"FFFF" else '0';
    data_final_dgt <= '1' when bit_cnt = data_bits_u + x"F" else '0';
    stop_final_dgt <= '1' when bit_cnt = stop_bits_u + x"F" else '0';

end architecture behavioral;