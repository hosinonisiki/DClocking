-- ///////////////Documentation////////////////////
-- Standard CORDIC algorithm.
-- Takes in both sine and cosine values and returns
-- an angle. Phase is normalized with x8000 representing
-- exactly +/- pi.

-- Reworked pipelining structure similar to trigonometric.vhdl.


library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity inv_trigonometric is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        -- data flow ports
        sin_in          :   in  std_logic_vector(15 downto 0);
        cos_in          :   in  std_logic_vector(15 downto 0);
        phase_out       :   out std_logic_vector(15 downto 0)
    );
end entity inv_trigonometric;

architecture behavioural of inv_trigonometric is
    signal sin_in_buf      :   signed(15 downto 0);
    signal cos_in_buf      :   signed(15 downto 0);
    signal phase_out_buf   :   signed(15 downto 0);

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
    signal c_pre, s_pre, z_pre  :   signed(23 downto 0); -- for pipelining
    signal c_buf, s_buf, z_buf  :   signed_array(0 to 17); -- buffers inserted to pipeline

    type sign_array is array(natural range <>) of std_logic;
    signal d, x             :   sign_array(0 to 18); -- d stores the sign of residue. x stores quandrant information of the input
    signal x_pre            :   std_logic; -- for pipelining
    signal d_buf, x_buf     :   sign_array(0 to 17); -- buffers inserted to pipeline

    signal sin_in_scaled    :   signed(31 downto 0);
    signal cos_in_scaled    :   signed(31 downto 0);
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    sin_in_buf  <= (others => '0');
                    cos_in_buf  <= (others => '0');
                else
                    sin_in_buf  <= signed(sin_in);
                    cos_in_buf  <= signed(cos_in);
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        sin_in_buf  <= (others => '0') when rst = '1' else signed(sin_in);
        cos_in_buf  <= (others => '0') when rst = '1' else signed(cos_in);
    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    phase_out   <= (others => '0');
                else
                    phase_out   <= std_logic_vector(phase_out_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        phase_out   <= (others => '0') when rst = '1' else std_logic_vector(phase_out_buf);
    end generate;

    -- To prevent overflow
    process(clk)
    begin
        if rising_edge(clk) then
            sin_in_scaled <= sin_in_buf * x"6DED";
            cos_in_scaled <= cos_in_buf * x"6DED";
        end if;
    end process;

    -- x(0) <= cos_in_scaled(31);
    x_pre <= cos_in_scaled(31);
    -- s(0) <= (sin_in_scaled(31 downto 8) xor x"FFFFFF") + x"000001" when x(0) = '1' else
    --         sin_in_scaled(31 downto 8);
    s_pre <= (sin_in_scaled(31 downto 8) xor x"FFFFFF") + x"000001" when x_pre = '1' else
            sin_in_scaled(31 downto 8);
    -- c(0) <= x"36F612" when cos_in_buf = x"0000" and sin_in_buf = x"0000" else
    --         (cos_in_scaled(31 downto 8) xor x"FFFFFF") + x"000001" when x(0) = '1' else
    --         cos_in_scaled(31 downto 8);
    c_pre <= x"36F612" when cos_in_buf = x"0000" and sin_in_buf = x"0000" else
            (cos_in_scaled(31 downto 8) xor x"FFFFFF") + x"000001" when x_pre = '1' else
            cos_in_scaled(31 downto 8);
    d(0) <= s_pre(23);
    -- z(0) <= - a(0) when d(0) = '1' else
    --         a(0);
    z_pre <= - a(0) when d(0) = '1' else
            a(0);

    process(clk)
    begin
        if rising_edge(clk) then
            if d(0) = '1' then
                c(0) <= c_pre - s_pre;
                s(0) <= s_pre + c_pre;
            else
                c(0) <= c_pre + s_pre;
                s(0) <= s_pre - c_pre;
            end if;
            x(0) <= x_pre;
            z(0) <= z_pre;
        end if;
    end process;

    iterations : for i in 0 to 17 generate
        c_buf(i) <= c(i) - shift_right(s(i), i + 1) when d_buf(i) = '1' else
                            c(i) + shift_right(s(i), i + 1);
        s_buf(i) <= s(i) + shift_right(c(i), i + 1) when d_buf(i) = '1' else
                            s(i) - shift_right(c(i), i + 1);
        d_buf(i) <= s(i)(23);
        x_buf(i) <= x(i);
        z_buf(i) <= z(i) - a(i + 1) when d_buf(i) = '1' else
                            z(i) + a(i + 1);
    end generate iterations;

    -- First layer requires one stage
    process(clk)
    begin
        if rising_edge(clk) then
            c(1) <= c_buf(0);
            s(1) <= s_buf(0);
            d(1) <= d_buf(0);
            x(1) <= x_buf(0);
            z(1) <= z_buf(0);
        end if;
    end process;

    no_buf_even : for i in 1 to 8 generate
        c(i * 2 + 1) <= c_buf(i * 2);
        s(i * 2 + 1) <= s_buf(i * 2);
        d(i * 2 + 1) <= d_buf(i * 2);
        x(i * 2 + 1) <= x_buf(i * 2);
        z(i * 2 + 1) <= z_buf(i * 2);
    end generate no_buf_even;

    buf_odd : for i in 0 to 8 generate
        process(clk)
        begin
            if rising_edge(clk) then
                c(i * 2 + 2) <= c_buf(i * 2 + 1);
                s(i * 2 + 2) <= s_buf(i * 2 + 1);
                d(i * 2 + 2) <= d_buf(i * 2 + 1);
                x(i * 2 + 2) <= x_buf(i * 2 + 1);
                z(i * 2 + 2) <= z_buf(i * 2 + 1);
            end if;
        end process;
    end generate buf_odd;

    phase_out_buf <= z(18)(23 downto 8) + x"8001" when z(18)(7) = '1' and x(18) = '1' else
                        z(18)(23 downto 8) + x"0001" when z(18)(7) = '1' and x(18) = '0' else
                        z(18)(23 downto 8) + x"8000" when z(18)(7) = '0' and x(18) = '1' else
                        z(18)(23 downto 8);
end architecture behavioural;






