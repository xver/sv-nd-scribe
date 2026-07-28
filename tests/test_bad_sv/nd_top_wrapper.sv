/*
 * Company: IC Verimeter
 * Author: Developer <dev@verimeter.com>
 * Description: Top wrapper without include guard
 */

`define small_macro 1

//Module: nd_top_wrapper
//Top wrapper module
module nd_top_wrapper;
	wire a, b;
  assign a = b;
  // This is an exceptionally long comment line that exceeds the maximum allowed character limit of 120 characters to trigger WKL-007 line length violation
endmodule : nd_top_wrapper
