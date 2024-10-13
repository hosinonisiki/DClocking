-- ///////////////Documentation////////////////////
-- Standard CORDIC algorithm.
-- Takes in a phase angle and returns both the sine
-- and cosine values. Phase is normalized with x8000
-- representing exactly +/- pi. altitude is normalized
-- with x7586a5 representing 1.0. Note that internal
-- signals are of 24 bits while io ports are 16 bits.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity trigonometric is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(63 downto 0);
        phase_in        :   in  std_logic_vector(15 downto 0);
        sin_out         :   out std_logic_vector(15 downto 0);
        cos_out         :   out std_logic_vector(15 downto 0)
    );
end entity trigonometric;

architecture behavioral of trigonometric is
    signal phase_in_buf     :   signed(15 downto 0);
    signal sin_out_buf      :   signed(15 downto 0);
    signal cos_out_buf      :   signed(15 downto 0);

    type signed_array is array(natural range <>) of signed(23 downto 0);
    -- Storing a variant for 18 iterations
    constant a              :   signed_array(0 to 18) := (
        x"200000",
        x"12e405",
        x"09fb38",
        x"051112",
        x"028b0d",
        x"0145d8",
        x"00a2f6",
        x"00517c",
        x"0028be",
        x"00145f",
        x"000a30",
        x"000518",
        x"00028c",
        x"000146",
        x"0000a3",
        x"000051",
        x"000029",
        x"000014",
        x"00000a"
    ); -- angle values of arctan(2^(-i))
    signal c, s, z          :   signed_array(0 to 18); -- cos, sin and angle residue
    signal c_buf, s_buf, z_buf  :   signed_array(0 to 17); -- buffers inserted to pipeline

    type sign_array is array(natural range <>) of std_logic;
    signal d, x             :   sign_array(0 to 18); -- d stores the sign of residue. x stores quandrant information of the input
    signal d_buf, x_buf     :   sign_array(0 to 17); -- buffers inserted to pipeline
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    phase_in_buf <= (others => '0');
                else
                    phase_in_buf <= signed(phase_in);
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        phase_in_buf <= (others => '0') when rst = '1' else signed(phase_in);
    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sin_out <= (others => '0');
                    cos_out <= (others => '0');
                else
                    sin_out <= std_logic_vector(sin_out_buf);
                    cos_out <= std_logic_vector(cos_out_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        sin_out <= (others => '0') when rst = '1' else std_logic_vector(sin_out_buf);
        cos_out <= (others => '0') when rst = '1' else std_logic_vector(cos_out_buf);
    end generate;

    -- rotate input angle to the first or fourth quadrant
    z(0) <= phase_in_buf(14) & phase_in_buf(14 downto 0) & x"00";
    x(0) <= phase_in_buf(15) xor phase_in_buf(14);
    d(0) <= z(0)(23);
    c(0) <= x"475e34"; -- x"475e34" = 0.607253 * x"7586a5", where 0.607253 is the product of cos(arctan(2^(-i))) for i = 0 to 18
    s(0) <= x"475e34" when d(0) = '0' else x"b8a1cc"; -- x"b8a1cc" = -0.607253 * x"7586a5"

    iterations : for i in 0 to 17 generate
        c_buf(i) <= c(i) - shift_right(s(i), i + 1) when d_buf(i) = '0' else
                            c(i) + shift_right(s(i), i + 1);
        s_buf(i) <= s(i) + shift_right(c(i), i + 1) when d_buf(i) = '0' else
                            s(i) - shift_right(c(i), i + 1);
        d_buf(i) <= z_buf(i)(23);
        x_buf(i) <= x(i);
        z_buf(i) <= z(i) - a(i) when d(i) = '0' else
                            z(i) + a(i);
        process(clk)
        begin
            if rising_edge(clk) then
                c(i + 1) <= c_buf(i);
                s(i + 1) <= s_buf(i);
                d(i + 1) <= d_buf(i);
                x(i + 1) <= x_buf(i);
                z(i + 1) <= z_buf(i);
            end if;
        end process;
    end generate iterations;

    -- rotate back to the original quadrant with rounding
    cos_out_buf <= c(18)(23 downto 8) xor x"FFFF" when c(18)(7) = '1' and x(18) = '1' else
                   c(18)(23 downto 8) + x"0001" when c(18)(7) = '1' and x(18) = '0' else
                   (c(18)(23 downto 8) xor x"FFFF") + x"0001" when c(18)(7) = '0' and x(18) = '1' else
                   c(18)(23 downto 8);
    sin_out_buf <= s(18)(23 downto 8) xor x"FFFF" when s(18)(7) = '1' and x(18) = '1' else
                   s(18)(23 downto 8) + x"0001" when s(18)(7) = '1' and x(18) = '0' else
                   (s(18)(23 downto 8) xor x"FFFF") + x"0001" when s(18)(7) = '0' and x(18) = '1' else
                   s(18)(23 downto 8);
end architecture behavioral;