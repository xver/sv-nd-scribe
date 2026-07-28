`ifndef ND_BIND_SV
`define ND_BIND_SV

// No header comment block (triggers ND-001 missing header)

bind nd_dut nd_protocol_checker checker_inst (
  .clk(clk),
  .rst_n(rst_n),
  .valid(valid)
);

`endif // ND_BIND_SV
