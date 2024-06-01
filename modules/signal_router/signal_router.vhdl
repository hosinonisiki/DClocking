-- ///////////////Documentation////////////////////
-- This project involves a large number of hardware
-- implemented apparatuses working on the FPGA.
-- In order to allow to connect them freely as if
-- they were real experimental devices, a router
-- module is added to direct the data flow between
-- them.

-- The router is set to have 64 input and output
-- ports each. Since this would result in a large
-- number of possible routings, instead of explicitly
-- defining all possible connections, the router
-- is devided into 8 smaller routers, each with 8
-- input and output ports, as well as 2 io ports
-- connected to a higher level router, which is
-- responsible for routing the data between the
-- smaller routers.

-- The outer router employs the standard 1024bit
-- parameter ram interface, as any other core
-- module in the project. Routing instructions
-- are read from the ram.

-- For the inner routers, consider one with 2**n io
-- ports for example. For each output port, an
-- address of n bits is needed to specify which
-- input port the data should be routed from. Also,
-- a 1 bit enable signal is needed. The total control
-- signal needed is (n+1)*2**n bits. For an 8 port
-- subrouter, 32 bits are required. For a 16 port
-- subrouter, 80 bits are required.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity signal_router is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(core_param_size - 1 downto 0);
        sig_in          :   in  signal_array(63 downto 0);
        sig_out         :   out signal_array(63 downto 0)
    );
end entity signal_router;

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity sub_router is
    generic(
        width : integer;
        log_width : integer -- ceiled
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        control_in      :   in  std_logic_vector((log_width + 1) * width - 1 downto 0);
        sig_in          :   in  signal_array(width - 1 downto 0);
        sig_out         :   out signal_array(width - 1 downto 0)
    );
end entity sub_router;

architecture structural of signal_router is
    signal sig_in_buf   :   signal_array(63 downto 0);
    signal sig_out_buf  :   signal_array(63 downto 0);

    signal sig_hin      :   signal_array(15 downto 0); -- higher level router
    signal sig_hout     :   signal_array(15 downto 0);
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk, rst)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sig_in_buf <= (others => (others => '0'));
                else
                    sig_in_buf <= sig_in;
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        sig_in_buf <= (others => (others => '0')) when rst = '1' else sig_in;
    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk, rst)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sig_out <= (others => (others => '0'));
                else
                    sig_out <= sig_out_buf;
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        sig_out <= (others => (others => '0')) when rst = '1' else sig_out_buf;
    end generate;

    banks : for i in 0 to 7 generate
        signal temp_in : signal_array(9 downto 0);
        signal temp_out : signal_array(9 downto 0);
    begin
        sub_router : entity work.sub_router generic map(
            width           =>  10,
            log_width       =>  4
        )port map(
            clk             =>  clk,
            rst             =>  rst,
            control_in      =>  core_param_in(50 * i + 49 downto 50 * i),
            sig_in          =>  temp_in,
            sig_out         =>  temp_out
        );
        temp_in(7 downto 0) <= sig_in_buf(8 * i + 7 downto 8 * i);
        temp_in(9 downto 8) <= sig_hout(2 * i + 1 downto 2 * i);
        sig_out_buf(8 * i + 7 downto 8 * i) <= temp_out(7 downto 0);
        sig_hin(2 * i + 1 downto 2 * i) <= temp_out(9 downto 8);
    end generate;

    higher_router : entity work.sub_router generic map(
        width               =>  16,
        log_width           =>  4
    )port map(
        clk                 =>  clk,
        rst                 =>  rst,
        control_in          =>  core_param_in(479 downto 400),
        sig_in              =>  sig_hin,
        sig_out             =>  sig_hout
    );
end architecture structural;

architecture behavioral of sub_router is
begin
    routings : for i in 0 to width - 1 generate
        process(clk)
        begin
            if rising_edge(clk) then
                if control_in(i * (log_width + 1) + log_width) = '0' then
                    sig_out(i) <= (others => '0');
                else 
                    sig_out(i) <= sig_in(to_integer(unsigned(control_in(i * (log_width + 1) + log_width - 1 downto i * (log_width + 1)))));
                end if;
            end if;
        end process;
    end generate;
end architecture behavioral;


