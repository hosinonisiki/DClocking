-- ///////////////Documentation////////////////////
-- This file describes a general template for modules
-- that are to be plugged into the top architecture.
-- The template contains an entity that describes the
-- core function of the module. A bus handler is used
-- to handle data from the bus and implement custom
-- logic. Also, a <> module is used to map parameters
-- onto the core entity's interface.

entity module_template is
    port(
        clk : in std_logic;
        rst : in std_logic;
        bus_en_in : in std_logic;
        dbus_in : in std_logic_vector(31 downto 0);
        abus_in : in std_logic_vector(9 downto 0);
        cbus_in : in std_logic_vector(7 downto 0);
        rsp_out : out std_logic_vector(31 downto 0);
        rsp_stat_out : out std_logic_vector(7 downto 0)
        -- data flow ports
    );
end entity module_template;

architecture structural of module_template is

begin

end architecture structural;