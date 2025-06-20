-- ///////////////Documentation////////////////////
-- Simple hardware button debouncer.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity debouncer is
    generic(
        debounce_time   : integer := 10; -- in ms
        default_output  : std_logic := '0' -- default value of output when reset
    );
    port(
        clk     : in  std_logic;
        rst     : in  std_logic;
        input   : in  std_logic;
        output  : out std_logic
    );
end entity debouncer;

architecture behavioral of debouncer is
    constant debounce_cycles            : integer := clk_freq / 1000 * debounce_time;
    constant debounce_cycles_unsigned   : unsigned(31 downto 0) := to_unsigned(debounce_cycles, 32);

    signal input_1      : std_logic := default_output;
    signal input_2      : std_logic := default_output;
    signal counter      : unsigned(31 downto 0) := (others => '0');
    signal input_stable : std_logic := '0';
begin
    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                counter <= (others => '0');
            else
                if input_stable = '0' and input_1 = input then
                    counter <= counter + x"00000001";
                else
                    counter <= (others => '0');
                end if;
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                input_stable <= '0';
            else
                if input_stable = '1' and input_1 /= input then
                    input_stable <= '0';
                elsif input_stable = '0' and counter = debounce_cycles_unsigned then
                    input_stable <= '1';
                end if;
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            if rst = '1' then
                output <= default_output;
            else
                if input_stable = '1' then
                    output <= input_2;
                end if;
            end if;
        end if;
    end process;

    process(clk)
    begin
        if rising_edge(clk) then
            input_1 <= input;
            input_2 <= input_1;
        end if;
    end process;
end architecture behavioral;