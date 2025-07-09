-- ///////////////Documentation////////////////////
-- This is a module that resembles the environment
-- of a moku cloud compile module, thus enables
-- the use of MCC instruments from the last project.
-- MCCs of different architectures are simultaneously
-- instantiated in the design.
-- Architectures are copied from the last project.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity mcc_wrapper is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(511 downto 0);
        inputa          :   in  std_logic_vector(15 downto 0);
        inputb          :   in  std_logic_vector(15 downto 0);
        outputa         :   out std_logic_vector(15 downto 0);
        outputb         :   out std_logic_vector(15 downto 0);
        outputc         :   out std_logic_vector(15 downto 0);
        outputd         :   out std_logic_vector(15 downto 0)
    );
end entity mcc_wrapper;

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

-- Definition of MCC CustomWrapper copied from
-- https://compile.liquidinstruments.com/docs/wrapper.html
entity customwrapper is
    port (
        clk         :   in std_logic;
        reset       :   in std_logic;

        inputa      :   in signed(15 downto 0);
        inputb      :   in signed(15 downto 0);

        outputa     :   out signed(15 downto 0);
        outputb     :   out signed(15 downto 0);
        outputc     :   out signed(15 downto 0);
        outputd     :   out signed(15 downto 0);

        control0    :   in std_logic_vector(31 downto 0);
        control1    :   in std_logic_vector(31 downto 0);
        control2    :   in std_logic_vector(31 downto 0);
        control3    :   in std_logic_vector(31 downto 0);
        control4    :   in std_logic_vector(31 downto 0);
        control5    :   in std_logic_vector(31 downto 0);
        control6    :   in std_logic_vector(31 downto 0);
        control7    :   in std_logic_vector(31 downto 0);
        control8    :   in std_logic_vector(31 downto 0);
        control9    :   in std_logic_vector(31 downto 0);
        control10   :   in std_logic_vector(31 downto 0);
        control11   :   in std_logic_vector(31 downto 0);
        control12   :   in std_logic_vector(31 downto 0);
        control13   :   in std_logic_vector(31 downto 0);
        control14   :   in std_logic_vector(31 downto 0);
        control15   :   in std_logic_vector(31 downto 0)
    );
end entity customwrapper;

architecture turnkey of mcc_wrapper is
    signal inputa_buf   :   signed(15 downto 0);
    signal inputb_buf   :   signed(15 downto 0);
    signal outputa_buf  :   signed(15 downto 0);
    signal outputb_buf  :   signed(15 downto 0);
    signal outputc_buf  :   signed(15 downto 0);
    signal outputd_buf  :   signed(15 downto 0);
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    inputa_buf <= (others => '0');
                    inputb_buf <= (others => '0');
                else
                    inputa_buf <= signed(inputa);
                    inputb_buf <= signed(inputb);
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        inputa_buf <= (others => '0') when rst = '1' else signed(inputa);
        inputb_buf <= (others => '0') when rst = '1' else signed(inputb);
    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    outputa <= (others => '0');
                    outputb <= (others => '0');
                    outputc <= (others => '0');
                    outputd <= (others => '0');
                else
                    outputa <= std_logic_vector(outputa_buf);
                    outputb <= std_logic_vector(outputb_buf);
                    outputc <= std_logic_vector(outputc_buf);
                    outputd <= std_logic_vector(outputd_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        outputa <= (others => '0') when rst = '1' else std_logic_vector(outputa_buf);
        outputb <= (others => '0') when rst = '1' else std_logic_vector(outputb_buf);
        outputc <= (others => '0') when rst = '1' else std_logic_vector(outputc_buf);
        outputd <= (others => '0') when rst = '1' else std_logic_vector(outputd_buf);
    end generate;

    mcc : entity work.customwrapper(turnkey) port map(
        clk => clk,
        reset => rst,

        inputa => inputa_buf,
        inputb => inputb_buf,

        outputa => outputa_buf,
        outputb => outputb_buf,
        outputc => outputc_buf,
        outputd => outputd_buf,

        control0 => core_param_in(31 downto 0),
        control1 => core_param_in(63 downto 32),
        control2 => core_param_in(95 downto 64),
        control3 => core_param_in(127 downto 96),
        control4 => core_param_in(159 downto 128),
        control5 => core_param_in(191 downto 160),
        control6 => core_param_in(223 downto 192),
        control7 => core_param_in(255 downto 224),
        control8 => core_param_in(287 downto 256),
        control9 => core_param_in(319 downto 288),
        control10 => core_param_in(351 downto 320),
        control11 => core_param_in(383 downto 352),
        control12 => core_param_in(415 downto 384),
        control13 => core_param_in(447 downto 416),
        control14 => core_param_in(479 downto 448),
        control15 => core_param_in(511 downto 480)
    );
end architecture turnkey;

architecture feedback of mcc_wrapper is
    signal inputa_buf   :   signed(15 downto 0);
    signal inputb_buf   :   signed(15 downto 0);
    signal outputa_buf  :   signed(15 downto 0);
    signal outputb_buf  :   signed(15 downto 0);
    signal outputc_buf  :   signed(15 downto 0);
    signal outputd_buf  :   signed(15 downto 0);
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    inputa_buf <= (others => '0');
                    inputb_buf <= (others => '0');
                else
                    inputa_buf <= signed(inputa);
                    inputb_buf <= signed(inputb);
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        inputa_buf <= (others => '0') when rst = '1' else signed(inputa);
        inputb_buf <= (others => '0') when rst = '1' else signed(inputb);
    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    outputa <= (others => '0');
                    outputb <= (others => '0');
                    outputc <= (others => '0');
                    outputd <= (others => '0');
                else
                    outputa <= std_logic_vector(outputa_buf);
                    outputb <= std_logic_vector(outputb_buf);
                    outputc <= std_logic_vector(outputc_buf);
                    outputd <= std_logic_vector(outputd_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        outputa <= (others => '0') when rst = '1' else std_logic_vector(outputa_buf);
        outputb <= (others => '0') when rst = '1' else std_logic_vector(outputb_buf);
        outputc <= (others => '0') when rst = '1' else std_logic_vector(outputc_buf);
        outputd <= (others => '0') when rst = '1' else std_logic_vector(outputd_buf);
    end generate;

    mcc : entity work.customwrapper(feedback) port map(
        clk => clk,
        reset => rst,

        inputa => inputa_buf,
        inputb => inputb_buf,

        outputa => outputa_buf,
        outputb => outputb_buf,
        outputc => outputc_buf,
        outputd => outputd_buf,

        control0 => core_param_in(31 downto 0),
        control1 => core_param_in(63 downto 32),
        control2 => core_param_in(95 downto 64),
        control3 => core_param_in(127 downto 96),
        control4 => core_param_in(159 downto 128),
        control5 => core_param_in(191 downto 160),
        control6 => core_param_in(223 downto 192),
        control7 => core_param_in(255 downto 224),
        control8 => core_param_in(287 downto 256),
        control9 => core_param_in(319 downto 288),
        control10 => core_param_in(351 downto 320),
        control11 => core_param_in(383 downto 352),
        control12 => core_param_in(415 downto 384),
        control13 => core_param_in(447 downto 416),
        control14 => core_param_in(479 downto 448),
        control15 => core_param_in(511 downto 480)
    );
end architecture feedback;

architecture PID_wrapped of mcc_wrapper is
    signal inputa_buf   :   signed(15 downto 0);
    signal inputb_buf   :   signed(15 downto 0);
    signal outputa_buf  :   signed(15 downto 0);
    signal outputb_buf  :   signed(15 downto 0);
    signal outputc_buf  :   signed(15 downto 0);
    signal outputd_buf  :   signed(15 downto 0);
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    inputa_buf <= (others => '0');
                    inputb_buf <= (others => '0');
                else
                    inputa_buf <= signed(inputa);
                    inputb_buf <= signed(inputb);
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        inputa_buf <= (others => '0') when rst = '1' else signed(inputa);
        inputb_buf <= (others => '0') when rst = '1' else signed(inputb);
    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    outputa <= (others => '0');
                    outputb <= (others => '0');
                    outputc <= (others => '0');
                    outputd <= (others => '0');
                else
                    outputa <= std_logic_vector(outputa_buf);
                    outputb <= std_logic_vector(outputb_buf);
                    outputc <= std_logic_vector(outputc_buf);
                    outputd <= std_logic_vector(outputd_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        outputa <= (others => '0') when rst = '1' else std_logic_vector(outputa_buf);
        outputb <= (others => '0') when rst = '1' else std_logic_vector(outputb_buf);
        outputc <= (others => '0') when rst = '1' else std_logic_vector(outputc_buf);
        outputd <= (others => '0') when rst = '1' else std_logic_vector(outputd_buf);
    end generate;

    mcc : entity work.customwrapper(PID_wrapped) port map(
        clk => clk,
        reset => rst,

        inputa => inputa_buf,
        inputb => inputb_buf,

        outputa => outputa_buf,
        outputb => outputb_buf,
        outputc => outputc_buf,
        outputd => outputd_buf,

        control0 => core_param_in(31 downto 0),
        control1 => core_param_in(63 downto 32),
        control2 => core_param_in(95 downto 64),
        control3 => core_param_in(127 downto 96),
        control4 => core_param_in(159 downto 128),
        control5 => core_param_in(191 downto 160),
        control6 => core_param_in(223 downto 192),
        control7 => core_param_in(255 downto 224),
        control8 => core_param_in(287 downto 256),
        control9 => core_param_in(319 downto 288),
        control10 => core_param_in(351 downto 320),
        control11 => core_param_in(383 downto 352),
        control12 => core_param_in(415 downto 384),
        control13 => core_param_in(447 downto 416),
        control14 => core_param_in(479 downto 448),
        control15 => core_param_in(511 downto 480)
    );
end architecture PID_wrapped;

architecture pdh of mcc_wrapper is
    signal inputa_buf   :   signed(15 downto 0);
    signal inputb_buf   :   signed(15 downto 0);
    signal outputa_buf  :   signed(15 downto 0);
    signal outputb_buf  :   signed(15 downto 0);
    signal outputc_buf  :   signed(15 downto 0);
    signal outputd_buf  :   signed(15 downto 0);
begin
    use_input_buffer : if io_buf = buf_for_io or io_buf = buf_i_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    inputa_buf <= (others => '0');
                    inputb_buf <= (others => '0');
                else
                    inputa_buf <= signed(inputa);
                    inputb_buf <= signed(inputb);
                end if;
            end if;
        end process;
    end generate;

    no_input_buffer : if io_buf = buf_o_only or io_buf = buf_none generate
        inputa_buf <= (others => '0') when rst = '1' else signed(inputa);
        inputb_buf <= (others => '0') when rst = '1' else signed(inputb);
    end generate;

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        process(clk)
        begin
            if rising_edge(clk) then
                if rst = '1' then
                    outputa <= (others => '0');
                    outputb <= (others => '0');
                    outputc <= (others => '0');
                    outputd <= (others => '0');
                else
                    outputa <= std_logic_vector(outputa_buf);
                    outputb <= std_logic_vector(outputb_buf);
                    outputc <= std_logic_vector(outputc_buf);
                    outputd <= std_logic_vector(outputd_buf);
                end if;
            end if;
        end process;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        outputa <= (others => '0') when rst = '1' else std_logic_vector(outputa_buf);
        outputb <= (others => '0') when rst = '1' else std_logic_vector(outputb_buf);
        outputc <= (others => '0') when rst = '1' else std_logic_vector(outputc_buf);
        outputd <= (others => '0') when rst = '1' else std_logic_vector(outputd_buf);
    end generate;

    mcc : entity work.customwrapper(pdh) port map(
        clk => clk,
        reset => rst,

        inputa => inputa_buf,
        inputb => inputb_buf,

        outputa => outputa_buf,
        outputb => outputb_buf,
        outputc => outputc_buf,
        outputd => outputd_buf,

        control0 => core_param_in(31 downto 0),
        control1 => core_param_in(63 downto 32),
        control2 => core_param_in(95 downto 64),
        control3 => core_param_in(127 downto 96),
        control4 => core_param_in(159 downto 128),
        control5 => core_param_in(191 downto 160),
        control6 => core_param_in(223 downto 192),
        control7 => core_param_in(255 downto 224),
        control8 => core_param_in(287 downto 256),
        control9 => core_param_in(319 downto 288),
        control10 => core_param_in(351 downto 320),
        control11 => core_param_in(383 downto 352),
        control12 => core_param_in(415 downto 384),
        control13 => core_param_in(447 downto 416),
        control14 => core_param_in(479 downto 448),
        control15 => core_param_in(511 downto 480)
    );
end architecture pdh;
