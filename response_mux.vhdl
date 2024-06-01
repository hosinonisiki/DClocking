-- ///////////////Documentation////////////////////
-- This design is used to select response from
-- different submodules and feed them to the main
-- control module. Which route will be selected
-- is decided by the control module.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity response_mux is
    generic(
        channel_count   :   integer
    );
    port(
        rbus_in         :   in  rbus_type;
        sbus_in         :   in  sbus_type;
        rsp_sel_in      :   in  std_logic_vector(mbus_w - 1 downto 0);
        rsp_out         :   out std_logic_vector(rbus_w - 1 downto 0);
        rsp_stat_out    :   out std_logic_vector(sbus_w - 1 downto 0)
    );
end entity response_mux;

architecture behavioral of response_mux is
begin
    rsp_out         <= rbus_in(to_integer(unsigned(rsp_sel_in))) when unsigned(rsp_sel_in) <= to_unsigned(channel_count, mbus_w) else (others => '0');
    rsp_stat_out    <= sbus_in(to_integer(unsigned(rsp_sel_in))) when unsigned(rsp_sel_in) <= to_unsigned(channel_count, mbus_w) else (others => '0');
end architecture behavioral;