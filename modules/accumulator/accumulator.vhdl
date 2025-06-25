-- ///////////////Documentation////////////////////
-- Simple accumulator providing stimulus for testing
-- purposes.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity accumulator is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(127 downto 0);
        acc_out         :   out std_logic_vector(15 downto 0);

        auto_reset_in   :   in  std_logic;
    );
end entity accumulator;

architecture behavioral of accumulator is
    signal delta        :   unsigned(63 downto 0);

    signal acc_out_buf  :   unsigned(15 downto 0);
    signal acc          :   unsigned(63 downto 0);

    signal internal_rst         :   std_logic;
    signal enable_auto_reset    :   std_logic;
begin
    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if internal_rst = '1' then
                    acc_out <= (others => '0');
                else
                    acc_out <= std_logic_vector(acc_out_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        acc_out <= (others => '0') when internal_rst = '1' else std_logic_vector(acc_out_buf);
    end generate;

    internal_rst <= '1' when rst = '1' or (enable_auto_reset = '1' and auto_reset_in = '1') else '0';

    delta <= unsigned(core_param_in(63 downto 0)); -- Address 0x00
    enable_auto_reset <= core_param_in(96); -- Address 0x03

    process(clk)
    begin
        if rising_edge(clk) then
            if internal_rst = '1' then
                acc <= (others => '0');
            else
                acc <= acc + delta;
            end if;
        end if;
    end process;
    acc_out_buf <= acc(63 downto 48);
end architecture behavioral;