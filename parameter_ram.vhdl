-- ///////////////Documentation////////////////////
-- This entity is used to read/write parameters
-- from/to a processing module. Because a module
-- needs to constantly read parameters from the
-- ram, the memory must be exposed to the module,
-- urging the need for a custom memory interface.
-- This entity provides an io interface to an
-- exposed memory.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity parameter_ram is
    generic(
        ram_default     :   std_logic_vector(core_param_size - 1 downto 0) := (others => '0')
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        wdata_in        :   in  std_logic_vector(dbus_w - 1 downto 0);
        waddr_in         :   in  std_logic_vector(abus_w - 1 downto 0);
        wmask_in        :   in  std_logic_vector(dbus_w - 1 downto 0);
        wval_in         :   in  std_logic;
        wen_in          :   in  std_logic;
        rdata_out       :   out std_logic_vector(dbus_w - 1 downto 0);
        raddr_in         :   in  std_logic_vector(abus_w - 1 downto 0);
        rval_out        :   out std_logic;
        ren_in          :   in  std_logic;
        ram_data_out    :   out std_logic_vector(core_param_size - 1 downto 0)
    );
end entity parameter_ram;

architecture behavioral of parameter_ram is
    signal ram_data     :   std_logic_vector(core_param_size - 1 downto 0) := ram_default;
    signal ram_buf      :   std_logic_vector(core_param_size - 1 downto 0) := ram_default;
begin
    
    process(clk, rst)
        variable waddr  : integer;
        variable target : std_logic_vector(dbus_w - 1 downto 0);
    begin
        if rising_edge(clk) then
            if rst = '1' then
                ram_data <= ram_default;
                ram_buf <= ram_default;
            else
                if wen_in = '1' then
                    waddr := to_integer(unsigned(waddr_in));
                    target := ram_buf(waddr * dbus_w + dbus_w - 1 downto waddr * dbus_w);
                    target <= (wmask_in and wdata_in) or ((not wmask_in) and target);
                end if;
                if wval_in = '1' then
                    ram_data <= ram_buf;
                end if;
            end if;
        end if;
    end process;

    process(clk, rst)
        variable raddr  : integer;
        variable target : std_logic_vector(dbus_w - 1 downto 0);
    begin
        if rising_edge(clk) then
            if rst = '1' then
                rval_out <= '0';
            else
                if ren_in = '1' then
                    raddr := to_integer(unsigned(raddr_in));
                    target := ram_data(raddr * dbus_w + dbus_w - 1 downto raddr * dbus_w);
                    rdata_out <= target;
                end if;
            end if;
        end if;
    end process;
    
    ram_data_out <= ram_data;

end architecture behavioral;
