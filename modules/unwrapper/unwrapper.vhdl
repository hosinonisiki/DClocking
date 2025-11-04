-- ///////////////Documentation////////////////////
-- Unwraps incoming signal and limits between 


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity unwrapper is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(63 downto 0);
        -- data flow ports
        sig_in          :   in  std_logic_vector(15 downto 0);
        sig_out         :   out std_logic_vector(15 downto 0);
        -- control ports
        auto_reset_in   :   in  std_logic -- Remove if the module does not need reset commands from other modules
    );
end entity unwrapper;

architecture behavioural of unwrapper is
    signal sig_in_buf           :   signed(15 downto 0);
    signal sig_out_buf          :   signed(15 downto 0);

    signal sig_in_buf_1         :   signed(15 downto 0);
    signal difference           :   signed(15 downto 0);
    signal unwrapped            :   signed(16 downto 0);
    signal unwrapped_buf        :   signed(16 downto 0);
    signal unwrapped_limited    :   signed(16 downto 0);

    signal internal_rst         :   std_logic;
    signal enable_auto_reset    :   std_logic;
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if internal_rst = '1' then
                    sig_in_buf <= (others => '0');
                else
                    sig_in_buf <= signed(sig_in);
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        sig_in_buf <= (others => '0') when internal_rst = '1' else signed(sig_in);
    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if internal_rst = '1' then
                    sig_out <= (others => '0');
                else
                    sig_out <= std_logic_vector(sig_out_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        sig_out <= (others => '0') when internal_rst = '1' else std_logic_vector(sig_out_buf);
    end generate;

    internal_rst <= '1' when rst = '1' or (enable_auto_reset = '1' and auto_reset_in = '1') else '0';
    enable_auto_reset <= core_param_in(32); -- address 0x01
    
    process(clk)
    begin
        if rising_edge(clk) then
            if internal_rst = '1' then
                sig_in_buf_1 <= (others => '0');
                unwrapped <= (others => '0');
            else
                sig_in_buf_1 <= sig_in_buf;
                unwrapped <= unwrapped_limited;
            end if;
        end if;
    end process;

    difference <= sig_in_buf - sig_in_buf_1;
    unwrapped_buf <= unwrapped + (difference(15) & difference);
    unwrapped_limited <= "00111111111111111" when unwrapped_buf(16 downto 15) = "01" else
                        "11000000000000000" when unwrapped_buf(16 downto 15) = "10" else
                        unwrapped_buf;

    sig_out_buf <= unwrapped_limited(15 downto 0);
end architecture behavioural;






