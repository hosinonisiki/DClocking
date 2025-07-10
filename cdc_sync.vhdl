-- ///////////////Documentation////////////////////
-- 1-bit CDC synchronizer.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity cdc_sync is
    generic(
        depth : integer := 2 -- Number of stages in the synchronizer
    );
    port(
        clk_src     : in std_logic; -- Source clock
        clk_dest    : in std_logic; -- Destination clock
        data_in     : in std_logic; -- Input data to synchronize
        data_out    : out std_logic -- Synchronized output data
    );
end entity cdc_sync;

architecture behavioural of cdc_sync is
    signal sync_stages  : std_logic_vector(depth - 1 downto 0) := (others => '0');

    -- Add ASYNC_REG attributes
begin
    process(clk_src)
    begin
        if rising_edge(clk_src) then
            sync_stages(0) <= data_in;
        end if;
    end process;

    gen : for i in 0 to depth - 2 generate
        process(clk_dest)
        begin
            if rising_edge(clk_dest) then
                sync_stages(i + 1) <= sync_stages(i);
            end if;
        end process;
    end generate;

    process(clk_dest)
    begin
        if rising_edge(clk_dest) then
            data_out <= sync_stages(depth - 1);
        end if;
    end process;
end architecture behavioural;