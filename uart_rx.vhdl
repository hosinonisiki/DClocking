-- ///////////////Documentation////////////////////
-- Simple uart receiver.

-- Uart/USB conversion done by CP2102-GM

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity uart_rx is
    generic(
        -- clk_freq and baudrate defined in mypak
        data_bits       :   integer := 8;
        stop_bits       :   integer := 1;
        parity_type     :   string  := "even" -- "none", "odd", "even", "mark", "space"
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        rxd_in          :   in  std_logic;
        dout            :   out std_logic_vector(data_bits - 1 downto 0) := (others => '0');
        dval_out        :   out std_logic := '0';
        idle_out        :   out std_logic := '1'
    );
end entity uart_rx;

architecture behavioral of uart_rx is
    constant data_bits_u        :   unsigned(3 downto 0) := to_unsigned(data_bits, 4);
    constant stop_bits_u        :   unsigned(3 downto 0) := to_unsigned(stop_bits, 4);
    constant bit_length         :   unsigned(15 downto 0) := to_unsigned(clk_freq / baudrate, 16); -- clock cycles per bit
    constant half_bit_length    :   unsigned(15 downto 0) := bit_length / 2; -- half bit length, used to sample in the middle of the bit

    type state_type is (s_idle, s_start, s_data, s_parity, s_stop, s_wait); -- in the case that '0' appears on the last stop bit, wait until '1' to enter idle state
    signal state                :   state_type := s_idle;
    signal last_state           :   state_type := s_idle;

    signal cycle_cnt            :   unsigned(15 downto 0); -- min baudrate 4800
    signal bit_cnt              :   unsigned(3 downto 0);

    signal data                 :   std_logic_vector(data_bits - 1 downto 0);
    signal valid                :   std_logic;
    signal parity               :   std_logic;
    signal bit_ready            :   std_logic;
    signal data_final_dgt       :   std_logic;
    signal stop_final_dgt       :   std_logic;
begin
    -- logic simplified from the original FSM
    -- state flow
    process(clk, rst)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                state <= s_idle;
            else
                case state is
                    when s_idle =>
                        if rxd_in = '0' then
                            state <= s_start;
                        end if;
                    when s_start =>
                        if bit_ready = '1' then
                            state <= s_data;
                        end if;
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
                            if rxd_in = '0' then
                                state <= s_wait;
                            else
                                state <= s_idle;
                            end if;
                        end if;
                    when s_wait =>
                        if rxd_in = '1' then
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
            if state = s_start or (state = s_stop and last_state /= s_stop) then
                bit_cnt <= x"0";
            elsif bit_ready = '1' then
                bit_cnt <= bit_cnt + x"1";
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_data and bit_ready = '1' then
                data(to_integer(bit_cnt)) <= rxd_in;
            end if;
        end if;
    end process;
    
    parity <= xor data;

    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_idle then
                valid <= '1';
            elsif state = s_parity and bit_ready = '1' and ((parity_type = "odd" and (parity xor rxd_in) = '0')
                                                                            or (parity_type = "even" and (parity xor rxd_in) = '1')
                                                                            or (parity_type = "mark" and rxd_in = '0')
                                                                            or (parity_type = "space" and rxd_in = '1')) then
                valid <= '0';
            elsif state = s_stop and bit_ready = '1' and rxd_in = '0' then
                valid <= '0';
            end if;
        end if;
    end process;

    dout <= data;

    process(clk)
    begin
        if rising_edge(clk) then
            if state = s_stop and bit_ready = '1' and stop_final_dgt = '1' and valid = '1' and rxd_in = '1' then
                dval_out <= '1';
            else
                dval_out <= '0';
            end if;
        end if;
    end process;

    idle_out <= '1' when state = s_idle and rst = '0' else '0';
    
    bit_ready <= '1' when cycle_cnt = bit_length + x"FFFF" or (state = s_start and cycle_cnt = half_bit_length + x"FFFF") else '0';
    data_final_dgt <= '1' when bit_cnt = data_bits_u + x"F" else '0';
    stop_final_dgt <= '1' when bit_cnt = stop_bits_u + x"F" else '0';

    -- process(clk, rst)
    -- begin
    --     if rising_edge(clk) then
    --         if rst = '1' then
    --             state <= idle;
    --         else
    --             case state is
    --                 when idle =>
    --                     dval_out <= '0';
    --                     if rxd_in = '0' then
    --                         cycle_cnt <= 0;
    --                         idle_out <= '0';
    --                         state <= start;
    --                     end if;
    --                 when start =>
    --                     if cycle_cnt = half_bit_length then
    --                         cycle_cnt <= 0;
    --                         bit_cnt <= 0;
    --                         data <= (others => '0');
    --                         parity <= '0';
    --                         state <= sample;
    --                     else
    --                         cycle_cnt <= cycle_cnt + 1;
    --                     end if;
    --                 when sample =>
    --                     if cycle_cnt = bit_length then
    --                         cycle_cnt <= 0;
    --                         data(bit_cnt) <= rxd_in;
    --                         parity <= parity xor rxd_in;
    --                         if bit_cnt = data_bits - 1 then
    --                             valid <= '1';
    --                             bit_cnt <= 0;
    --                             if parity_type = "none" then
    --                                 state <= stop;
    --                             else
    --                                 state <= verify;
    --                             end if;
    --                         else
    --                             bit_cnt <= bit_cnt + 1;
    --                         end if;
    --                     else
    --                         cycle_cnt <= cycle_cnt + 1;
    --                     end if;
    --                 when verify =>
    --                     if cycle_cnt = bit_length then
    --                         cycle_cnt <= 0;
    --                         case parity_type is
    --                             when "odd" =>
    --                                 if (parity xor rxd_in) = '0' then
    --                                     valid <= '0';
    --                                 end if;
    --                             when "even" =>
    --                                 if (parity xor rxd_in) = '1' then
    --                                     valid <= '0';
    --                                 end if;
    --                             when "mark" =>
    --                                 if rxd_in = '0' then
    --                                     valid <= '0';
    --                                 end if;
    --                             when "space" =>
    --                                 if rxd_in = '1' then
    --                                     valid <= '0';
    --                                 end if;
    --                         end case;
    --                         state <= stop;
    --                     else
    --                         cycle_cnt <= cycle_cnt + 1;
    --                     end if;
    --                 when stop =>
    --                     if cycle_cnt = bit_length then
    --                         cycle_cnt <= 0;
    --                         if rxd_in = '0' then
    --                             valid <= '0';
    --                         end if;
    --                         if bit_cnt = stop_bits - 1 then
    --                             if valid = '1' then
    --                                 dout <= data;
    --                                 dval_out <= '1';
    --                             end if;
    --                             idle_out <= '1';
    --                             state <= idle;
    --                         else
    --                             bit_cnt <= bit_cnt + 1;
    --                         end if;
    --                     else
    --                         cycle_cnt <= cycle_cnt + 1;
    --                     end if;
    --                 when others =>
    --                     state <= idle;
    --             end case;
    --         end if;
    --     end if;
    -- end process;
end architecture behavioral;