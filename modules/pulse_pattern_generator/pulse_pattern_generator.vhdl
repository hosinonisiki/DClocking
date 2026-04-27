-- ///////////////Documentation////////////////////
-- Generates a pulse pattern composed of up to 8 line
-- segments. The module is controlled by one wire:
-- a rising edge starts a pattern, and the wire level
-- is checked only at the end of each full pattern cycle.
--
-- While the pattern is active, parameters are held in
-- internal registers so bus writes do not disturb the
-- waveform. Each segment is defined by a starting point,
-- a duration, and a slope. At the end of each full cycle,
-- the waveform stops if the control wire is low or the
-- configured repeat count has been reached.
--
-- A segment with zero duration is treated as an invalid
-- configuration and stops the waveform cleanly.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.mypak.all;

entity pulse_pattern_generator is
    generic(
        io_buf : buf_type := buf_for_io
    );
    port(
        clk             :   in  std_logic;
        rst             :   in  std_logic;
        core_param_in   :   in  std_logic_vector(1023 downto 0);
        sig_out         :   out std_logic_vector(15 downto 0)
    );
end entity pulse_pattern_generator;

architecture behavioral of pulse_pattern_generator is
    type duration_array_type is array (0 to 7) of unsigned(31 downto 0);
    type start_array_type is array (0 to 7) of signed(15 downto 0);
    type slope_array_type is array (0 to 7) of signed(31 downto 0);

    signal control_wire_in      : std_logic;
    signal repeat_count_in      : unsigned(31 downto 0);
    signal segment_count_in     : unsigned(3 downto 0);
    signal idle_level_in        : signed(15 downto 0);
    signal segment_duration_in  : duration_array_type := (others => (others => '0'));
    signal segment_start_in     : start_array_type := (others => (others => '0'));
    signal segment_slope_in     : slope_array_type := (others => (others => '0'));

    signal repeat_count_reg     : unsigned(31 downto 0) := (others => '0');
    signal segment_count_reg    : unsigned(3 downto 0) := (others => '0');
    signal idle_level_reg       : signed(15 downto 0) := (others => '0');
    signal segment_duration_reg : duration_array_type := (others => (others => '0'));
    signal segment_start_reg    : start_array_type := (others => (others => '0'));
    signal segment_slope_reg    : slope_array_type := (others => (others => '0'));

    signal current_slope        : signed(31 downto 0) := (others => '0');
    signal next_duration        : unsigned(31 downto 0) := (others => '0');
    signal next_start           : signed(15 downto 0) := (others => '0');

    signal control_prev         : std_logic := '0';
    signal active               : std_logic := '0';
    signal cycle_count          : unsigned(31 downto 0) := (others => '0');
    signal segment_index        : unsigned(2 downto 0) := (others => '0');
    signal cycles_remaining     : unsigned(31 downto 0) := (others => '0');
    signal current_level_fp     : signed(31 downto 0) := (others => '0');
    signal idle_level_fp        : signed(31 downto 0) := (others => '0');
    signal segment0_start_fp    : signed(31 downto 0) := (others => '0');
    signal next_start_fp        : signed(31 downto 0) := (others => '0');
    signal sig_out_buf          : std_logic_vector(15 downto 0) := (others => '0');
begin
    control_wire_in <= core_param_in(0); -- address 0x00
    repeat_count_in <= unsigned(core_param_in(127 downto 96)); -- address 0x03
    segment_count_in <= unsigned(core_param_in(131 downto 128)); -- address 0x04
    idle_level_in <= signed(core_param_in(207 downto 192)); -- address 0x06

    segment_map : for i in 0 to 7 generate
    begin
        segment_duration_in(i) <= unsigned(core_param_in(32 * (8 + 3 * i) + 31 downto 32 * (8 + 3 * i))); -- address 0x08 + 3*i
        segment_start_in(i) <= signed(core_param_in(32 * (9 + 3 * i) + 15 downto 32 * (9 + 3 * i))); -- address 0x09 + 3*i
        segment_slope_in(i) <= signed(core_param_in(32 * (10 + 3 * i) + 31 downto 32 * (10 + 3 * i))); -- address 0x0A + 3*i
    end generate;

    with segment_index select current_slope <=
        segment_slope_reg(0) when "000",
        segment_slope_reg(1) when "001",
        segment_slope_reg(2) when "010",
        segment_slope_reg(3) when "011",
        segment_slope_reg(4) when "100",
        segment_slope_reg(5) when "101",
        segment_slope_reg(6) when "110",
        segment_slope_reg(7) when others;

    with segment_index select next_duration <=
        segment_duration_reg(1) when "000",
        segment_duration_reg(2) when "001",
        segment_duration_reg(3) when "010",
        segment_duration_reg(4) when "011",
        segment_duration_reg(5) when "100",
        segment_duration_reg(6) when "101",
        segment_duration_reg(7) when "110",
        segment_duration_reg(0) when others;

    with segment_index select next_start <=
        segment_start_reg(1) when "000",
        segment_start_reg(2) when "001",
        segment_start_reg(3) when "010",
        segment_start_reg(4) when "011",
        segment_start_reg(5) when "100",
        segment_start_reg(6) when "101",
        segment_start_reg(7) when "110",
        segment_start_reg(0) when others;

    idle_level_fp <= idle_level_reg & x"0000";
    segment0_start_fp <= segment_start_reg(0) & x"0000";
    next_start_fp <= next_start & x"0000";
    sig_out_buf <= std_logic_vector(idle_level_reg) when active = '0' else std_logic_vector(current_level_fp(31 downto 16));

    use_output_buffer : if io_buf = buf_for_io or io_buf = buf_o_only generate
        sig_out <= (others => '0') when rst = '1' else sig_out_buf;
    end generate;

    no_output_buffer : if io_buf = buf_i_only or io_buf = buf_none generate
        process(rst, current_level_fp)
        begin
            if rst = '1' then
                sig_out <= (others => '0');
            else
                sig_out <= std_logic_vector(current_level_fp(31 downto 16));
            end if;
        end process;
    end generate;

    process(clk)
        variable segment_count_v : integer;
        variable segment_index_v : integer;
        variable next_level_v    : signed(31 downto 0);
    begin
        if rising_edge(clk) then
            if rst = '1' then
                control_prev <= '0';
                active <= '0';
                cycle_count <= (others => '0');
                segment_index <= (others => '0');
                cycles_remaining <= (others => '0');
                current_level_fp <= (others => '0');
                repeat_count_reg <= (others => '0');
                segment_count_reg <= (others => '0');
                idle_level_reg <= (others => '0');
                segment_duration_reg <= (others => (others => '0'));
                segment_start_reg <= (others => (others => '0'));
                segment_slope_reg <= (others => (others => '0'));
            else
                if active = '0' then
                    repeat_count_reg <= repeat_count_in;
                    if segment_count_in > to_unsigned(8, 4) then
                        segment_count_reg <= to_unsigned(8, 4);
                    else
                        segment_count_reg <= segment_count_in;
                    end if;
                    idle_level_reg <= idle_level_in;
                    segment_duration_reg <= segment_duration_in;
                    segment_start_reg <= segment_start_in;
                    segment_slope_reg <= segment_slope_in;
                    current_level_fp <= idle_level_in & x"0000";

                    if control_wire_in = '1' and control_prev = '0' then
                        if segment_count_in = to_unsigned(0, 4) or segment_duration_in(0) = to_unsigned(0, 32) then
                            active <= '0';
                            cycle_count <= (others => '0');
                            segment_index <= (others => '0');
                            cycles_remaining <= (others => '0');
                            current_level_fp <= idle_level_in & x"0000";
                        else
                            active <= '1';
                            cycle_count <= to_unsigned(1, 32);
                            segment_index <= (others => '0');
                            cycles_remaining <= segment_duration_in(0) - 1;
                            current_level_fp <= segment_start_in(0) & x"0000";
                        end if;
                    end if;
                else
                    segment_count_v := to_integer(segment_count_reg);
                    segment_index_v := to_integer(segment_index);

                    if cycles_remaining = 0 then
                        if segment_index_v + 1 < segment_count_v then
                            if next_duration = to_unsigned(0, 32) then
                                active <= '0';
                                cycle_count <= (others => '0');
                                segment_index <= (others => '0');
                                cycles_remaining <= (others => '0');
                                current_level_fp <= idle_level_fp;
                            else
                                segment_index <= segment_index + 1;
                                cycles_remaining <= next_duration - 1;
                                current_level_fp <= next_start_fp;
                            end if;
                        else
                            if repeat_count_reg /= to_unsigned(0, 32) and cycle_count >= repeat_count_reg then
                                active <= '0';
                                cycle_count <= (others => '0');
                                segment_index <= (others => '0');
                                cycles_remaining <= (others => '0');
                                current_level_fp <= idle_level_fp;
                            elsif control_wire_in = '1' then
                                if segment_duration_reg(0) = to_unsigned(0, 32) then
                                    active <= '0';
                                    cycle_count <= (others => '0');
                                    segment_index <= (others => '0');
                                    cycles_remaining <= (others => '0');
                                    current_level_fp <= idle_level_fp;
                                else
                                    cycle_count <= cycle_count + 1;
                                    segment_index <= (others => '0');
                                    cycles_remaining <= segment_duration_reg(0) - 1;
                                    current_level_fp <= segment0_start_fp;
                                end if;
                            else
                                active <= '0';
                                cycle_count <= (others => '0');
                                segment_index <= (others => '0');
                                cycles_remaining <= (others => '0');
                                current_level_fp <= idle_level_fp;
                            end if;
                        end if;
                    else
                        next_level_v := current_level_fp + current_slope;
                        current_level_fp <= next_level_v;
                        cycles_remaining <= cycles_remaining - 1;
                    end if;
                end if;

                control_prev <= control_wire_in;
            end if;
        end if;
    end process;
end architecture behavioral;
