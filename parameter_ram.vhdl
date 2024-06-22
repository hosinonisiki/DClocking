-- ///////////////Documentation////////////////////
-- This entity is used to read/write parameters
-- from/to a processing module. Because a module
-- needs to constantly read parameters from the
-- ram, the memory must be exposed to the module,
-- urging the need for a custom memory interface.
-- This entity provides an io interface to an
-- exposed memory.

-- ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓1024 bit size↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity parameter_ram_1024 is
    generic(
        ram_default     :   std_logic_vector(1023 downto 0) := (others => '0')
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        wdata_in        :   in  std_logic_vector(dbus_w - 1 downto 0);
        waddr_in        :   in  std_logic_vector(abus_w - 1 downto 0);
        wmask_in        :   in  std_logic_vector(dbus_w - 1 downto 0);
        wval_in         :   in  std_logic;
        wen_in          :   in  std_logic;
        rdata_out       :   out std_logic_vector(dbus_w - 1 downto 0);
        raddr_in        :   in  std_logic_vector(abus_w - 1 downto 0);
        rval_out        :   out std_logic;
        ren_in          :   in  std_logic;
        ram_data_out    :   out std_logic_vector(1023 downto 0)
    );
end entity parameter_ram_1024;

architecture behavioral of parameter_ram_1024 is
    constant log_ram_size   : integer := 10;
    constant abus_w_val     : integer := log_ram_size - log_dbus_w; -- Valid address width, using the LSBs of the address

    signal ram_data         :   std_logic_vector(1023 downto 0) := ram_default;
    signal ram_buf          :   std_logic_vector(1023 downto 0) := ram_default;
begin
    
    process(clk, rst)
        variable waddr  : integer;
    begin
        if rising_edge(clk) then
            if rst = '1' then
                ram_data <= ram_default;
                ram_buf <= ram_default;
            else
                if wen_in = '1' then
                    waddr := to_integer(unsigned(waddr_in(abus_w_val - 1 downto 0)));
                    ram_buf(waddr * dbus_w + dbus_w - 1 downto waddr * dbus_w) <= (wmask_in and wdata_in) or ((not wmask_in) and ram_buf(waddr * dbus_w + dbus_w - 1 downto waddr * dbus_w));
                end if;
                if wval_in = '1' then
                    ram_data <= ram_buf;
                end if;
            end if;
        end if;
    end process;

    process(clk, rst)
        variable raddr  : integer;
    begin
        if rising_edge(clk) then
            if rst = '1' then
                rval_out <= '0';
            else
                rval_out <= ren_in;
                if ren_in = '1' then
                    raddr := to_integer(unsigned(raddr_in(abus_w_val - 1 downto 0)));
                    rdata_out <= ram_data(raddr * dbus_w + dbus_w - 1 downto raddr * dbus_w);
                end if;
            end if;
        end if;
    end process;
    
    ram_data_out <= ram_data;

end architecture behavioral;

-- ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑1024 bit size↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑

-- ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓512 bit size↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity parameter_ram_512 is
    generic(
        ram_default     :   std_logic_vector(511 downto 0) := (others => '0')
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        wdata_in        :   in  std_logic_vector(dbus_w - 1 downto 0);
        waddr_in        :   in  std_logic_vector(abus_w - 1 downto 0);
        wmask_in        :   in  std_logic_vector(dbus_w - 1 downto 0);
        wval_in         :   in  std_logic;
        wen_in          :   in  std_logic;
        rdata_out       :   out std_logic_vector(dbus_w - 1 downto 0);
        raddr_in        :   in  std_logic_vector(abus_w - 1 downto 0);
        rval_out        :   out std_logic;
        ren_in          :   in  std_logic;
        ram_data_out    :   out std_logic_vector(511 downto 0)
    );
end entity parameter_ram_512;

architecture behavioral of parameter_ram_512 is
    constant log_ram_size   : integer := 9;
    constant abus_w_val     : integer := log_ram_size - log_dbus_w; -- Valid address width, using the LSBs of the address

    signal ram_data     :   std_logic_vector(511 downto 0) := ram_default;
    signal ram_buf      :   std_logic_vector(511 downto 0) := ram_default;
begin
    
    process(clk, rst)
        variable waddr  : integer;
    begin
        if rising_edge(clk) then
            if rst = '1' then
                ram_data <= ram_default;
                ram_buf <= ram_default;
            else
                if wen_in = '1' then
                    waddr := to_integer(unsigned(waddr_in(abus_w_val - 1 downto 0)));
                    ram_buf(waddr * dbus_w + dbus_w - 1 downto waddr * dbus_w) <= (wmask_in and wdata_in) or ((not wmask_in) and ram_buf(waddr * dbus_w + dbus_w - 1 downto waddr * dbus_w));
                end if;
                if wval_in = '1' then
                    ram_data <= ram_buf;
                end if;
            end if;
        end if;
    end process;

    process(clk, rst)
        variable raddr  : integer;
    begin
        if rising_edge(clk) then
            if rst = '1' then
                rval_out <= '0';
            else
                rval_out <= ren_in;
                if ren_in = '1' then
                    raddr := to_integer(unsigned(raddr_in(abus_w_val - 1 downto 0)));
                    rdata_out <= ram_data(raddr * dbus_w + dbus_w - 1 downto raddr * dbus_w);
                end if;
            end if;
        end if;
    end process;
    
    ram_data_out <= ram_data;

end architecture behavioral;

-- ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑512 bit size↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑

-- ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓256 bit size↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity parameter_ram_256 is
    generic(
        ram_default     :   std_logic_vector(255 downto 0) := (others => '0')
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        wdata_in        :   in  std_logic_vector(dbus_w - 1 downto 0);
        waddr_in        :   in  std_logic_vector(abus_w - 1 downto 0);
        wmask_in        :   in  std_logic_vector(dbus_w - 1 downto 0);
        wval_in         :   in  std_logic;
        wen_in          :   in  std_logic;
        rdata_out       :   out std_logic_vector(dbus_w - 1 downto 0);
        raddr_in        :   in  std_logic_vector(abus_w - 1 downto 0);
        rval_out        :   out std_logic;
        ren_in          :   in  std_logic;
        ram_data_out    :   out std_logic_vector(255 downto 0)
    );
end entity parameter_ram_256;

architecture behavioral of parameter_ram_256 is
    constant log_ram_size   : integer := 8;
    constant abus_w_val     : integer := log_ram_size - log_dbus_w; -- Valid address width, using the LSBs of the address

    signal ram_data     :   std_logic_vector(255 downto 0) := ram_default;
    signal ram_buf      :   std_logic_vector(255 downto 0) := ram_default;
begin
    
    process(clk, rst)
        variable waddr  : integer;
    begin
        if rising_edge(clk) then
            if rst = '1' then
                ram_data <= ram_default;
                ram_buf <= ram_default;
            else
                if wen_in = '1' then
                    waddr := to_integer(unsigned(waddr_in(abus_w_val - 1 downto 0)));
                    ram_buf(waddr * dbus_w + dbus_w - 1 downto waddr * dbus_w) <= (wmask_in and wdata_in) or ((not wmask_in) and ram_buf(waddr * dbus_w + dbus_w - 1 downto waddr * dbus_w));
                end if;
                if wval_in = '1' then
                    ram_data <= ram_buf;
                end if;
            end if;
        end if;
    end process;

    process(clk, rst)
        variable raddr  : integer;
    begin
        if rising_edge(clk) then
            if rst = '1' then
                rval_out <= '0';
            else
                rval_out <= ren_in;
                if ren_in = '1' then
                    raddr := to_integer(unsigned(raddr_in(abus_w_val - 1 downto 0)));
                    rdata_out <= ram_data(raddr * dbus_w + dbus_w - 1 downto raddr * dbus_w);
                end if;
            end if;
        end if;
    end process;
    
    ram_data_out <= ram_data;

end architecture behavioral;

-- ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑256 bit size↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑

-- ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓128 bit size↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity parameter_ram_128 is
    generic(
        ram_default     :   std_logic_vector(127 downto 0) := (others => '0')
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        wdata_in        :   in  std_logic_vector(dbus_w - 1 downto 0);
        waddr_in        :   in  std_logic_vector(abus_w - 1 downto 0);
        wmask_in        :   in  std_logic_vector(dbus_w - 1 downto 0);
        wval_in         :   in  std_logic;
        wen_in          :   in  std_logic;
        rdata_out       :   out std_logic_vector(dbus_w - 1 downto 0);
        raddr_in        :   in  std_logic_vector(abus_w - 1 downto 0);
        rval_out        :   out std_logic;
        ren_in          :   in  std_logic;
        ram_data_out    :   out std_logic_vector(127 downto 0)
    );
end entity parameter_ram_128;

architecture behavioral of parameter_ram_128 is
    constant log_ram_size   : integer := 7;
    constant abus_w_val     : integer := log_ram_size - log_dbus_w; -- Valid address width, using the LSBs of the address

    signal ram_data     :   std_logic_vector(127 downto 0) := ram_default;
    signal ram_buf      :   std_logic_vector(127 downto 0) := ram_default;
begin
    
    process(clk, rst)
        variable waddr  : integer;
    begin
        if rising_edge(clk) then
            if rst = '1' then
                ram_data <= ram_default;
                ram_buf <= ram_default;
            else
                if wen_in = '1' then
                    waddr := to_integer(unsigned(waddr_in(abus_w_val - 1 downto 0)));
                    ram_buf(waddr * dbus_w + dbus_w - 1 downto waddr * dbus_w) <= (wmask_in and wdata_in) or ((not wmask_in) and ram_buf(waddr * dbus_w + dbus_w - 1 downto waddr * dbus_w));
                end if;
                if wval_in = '1' then
                    ram_data <= ram_buf;
                end if;
            end if;
        end if;
    end process;

    process(clk, rst)
        variable raddr  : integer;
    begin
        if rising_edge(clk) then
            if rst = '1' then
                rval_out <= '0';
            else
                rval_out <= ren_in;
                if ren_in = '1' then
                    raddr := to_integer(unsigned(raddr_in(abus_w_val - 1 downto 0)));
                    rdata_out <= ram_data(raddr * dbus_w + dbus_w - 1 downto raddr * dbus_w);
                end if;
            end if;
        end if;
    end process;
    
    ram_data_out <= ram_data;

end architecture behavioral;

-- ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑128 bit size↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑

-- ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓64 bit size↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity parameter_ram_64 is
    generic(
        ram_default     :   std_logic_vector(63 downto 0) := (others => '0')
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        wdata_in        :   in  std_logic_vector(dbus_w - 1 downto 0);
        waddr_in        :   in  std_logic_vector(abus_w - 1 downto 0);
        wmask_in        :   in  std_logic_vector(dbus_w - 1 downto 0);
        wval_in         :   in  std_logic;
        wen_in          :   in  std_logic;
        rdata_out       :   out std_logic_vector(dbus_w - 1 downto 0);
        raddr_in        :   in  std_logic_vector(abus_w - 1 downto 0);
        rval_out        :   out std_logic;
        ren_in          :   in  std_logic;
        ram_data_out    :   out std_logic_vector(63 downto 0)
    );
end entity parameter_ram_64;

architecture behavioral of parameter_ram_64 is
    constant log_ram_size   : integer := 6;
    constant abus_w_val     : integer := log_ram_size - log_dbus_w; -- Valid address width, using the LSBs of the address

    signal ram_data     :   std_logic_vector(63 downto 0) := ram_default;
    signal ram_buf      :   std_logic_vector(63 downto 0) := ram_default;
begin
    
    process(clk, rst)
        variable waddr  : integer;
    begin
        if rising_edge(clk) then
            if rst = '1' then
                ram_data <= ram_default;
                ram_buf <= ram_default;
            else
                if wen_in = '1' then
                    waddr := to_integer(unsigned(waddr_in(abus_w_val - 1 downto 0)));
                    ram_buf(waddr * dbus_w + dbus_w - 1 downto waddr * dbus_w) <= (wmask_in and wdata_in) or ((not wmask_in) and ram_buf(waddr * dbus_w + dbus_w - 1 downto waddr * dbus_w));
                end if;
                if wval_in = '1' then
                    ram_data <= ram_buf;
                end if;
            end if;
        end if;
    end process;

    process(clk, rst)
        variable raddr  : integer;
    begin
        if rising_edge(clk) then
            if rst = '1' then
                rval_out <= '0';
            else
                rval_out <= ren_in;
                if ren_in = '1' then
                    raddr := to_integer(unsigned(raddr_in(abus_w_val - 1 downto 0)));
                    rdata_out <= ram_data(raddr * dbus_w + dbus_w - 1 downto raddr * dbus_w);
                end if;
            end if;
        end if;
    end process;
    
    ram_data_out <= ram_data;

end architecture behavioral;

-- ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑64 bit size↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
