`timescale 1ns / 1ps
`default_nettype none
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date:    23:23:42 07/16/2013 
// Design Name: 
// Module Name:    util 
// Project Name: 
// Target Devices: 
// Tool versions: 
// Description: 
//
// Dependencies: 
//
// Revision: 
// Revision 0.01 - File Created
// Additional Comments: 
//
//////////////////////////////////////////////////////////////////////////////////

module sseg #(parameter N=18) (
		input wire clk,
		input wire [15:0] in,
		output reg [7:0] c,
		output reg [3:0] an
	);
	/**
	A simple seven-segment display driver, designed for the display on the Nexys 3.
	
	N: the driver will iterate over all four digits every 2**N clock cycles
	clk: the clock that is the source of timing for switching between digits
	in: a 16-bit value; each of the 4-bit nibbles will be put onto the display, msb leftmost
	c: an 8-bit output determining the segments to display.  active low.
	an: a 4-bit output determining the characters to enable.  active low.
	
	With a 10MHz clock I've been using N=16, which gives a full cycle every 6ms
	**/

	reg [N-1:0] ctr; // counter that determines which digit to display
	always @(posedge clk) begin
		ctr <= ctr + 1'b1;
	end
	
	wire [1:0] digit; // use the top two bits of the counter as the digit identifier
	assign digit = ctr[N-1:N-2];
	
	reg [3:0] val;
	always @(*) begin
		an = 4'b1111;
		an[digit] = 0;
		// select the values for the digit:
		case (digit)
			2'b00: val = in[3:0];
			2'b01: val = in[7:4];
			2'b10: val = in[11:8];
			2'b11: val = in[15:12];
		endcase

		// map that to a segment map:
		case(val)
			4'b0000: c = 8'b11000000;
			4'b0001: c = 8'b11111001;
			4'b0010: c = 8'b10100100;
			4'b0011: c = 8'b10110000;
			4'b0100: c = 8'b10011001;
			4'b0101: c = 8'b10010010;
			4'b0110: c = 8'b10000010;
			4'b0111: c = 8'b11111000;
			4'b1000: c = 8'b10000000;
			4'b1001: c = 8'b10010000;
			4'b1010: c = 8'b10001000;
			4'b1011: c = 8'b10000011;
			4'b1100: c = 8'b10100111;
			4'b1101: c = 8'b10100001;
			4'b1110: c = 8'b10000110;
			4'b1111: c = 8'b10001110;
			default: c = 8'b10110110;
		endcase
	end
endmodule

module debounce #(parameter B=16) (
		input wire clk,
		input wire in,
		output reg out
	);
	
	reg prev;
	reg [B:0] ctr;
	reg _o; // pipeline register for out
	always @(posedge clk) begin
		ctr <= ctr + 1'b1;
		out <= _o;
		if (ctr[B]) begin
			_o <= in;
		end
		if (in != prev) begin
			prev <= in;
			ctr <= 0;
		end
	end
endmodule

module debounce_unopt #(parameter N=100000) (
		input wire clk,
		input wire in,
		output reg out
	);
	
	reg prev;
	reg [16:0] ctr;
	reg _o; // pipeline register for out
	always @(posedge clk) begin
		if (in != prev) begin
			prev <= in;
			ctr <= 0;
		end else if (ctr == N) begin
			_o <= in;
		end else begin
			ctr <= ctr + 1;
		end
		out <= _o;
	end
endmodule


module uart_transmitter #(parameter CLK_CYCLES=4167, CTR_WIDTH=16)
		(input wire clk, input wire [7:0] data, input wire req, output wire ready, output wire uart_tx);
		
		reg [CTR_WIDTH-1:0] ctr;
		
		reg [9:0] line_data = 10'b1111111111;
		reg [4:0] bits_left;
		
		initial begin
			ctr = 0;
			bits_left = 0;
		end;
		
		assign uart_tx = line_data[0];
		assign ready = (bits_left == 0);
		
		always @(posedge clk) begin
			ctr <= ctr + 1'b1;
			
			if (ctr == (CLK_CYCLES-1)) begin
				ctr <= 0;
				
				// pop off the just-sent bit (index 0) and shift in a 1:
				line_data <= {1'b1, line_data[9:1]};
				
				if (bits_left != 0)
					bits_left <= bits_left - 1'b1;
			end
				
			if (req && ready) begin
				line_data <= {1'b1, data, 1'b0};
				ctr <= 0;
				bits_left <= 4'd10;
			end
		end
endmodule

module uart_multibyte_transmitter #(parameter CLK_CYCLES=4167, CTR_WIDTH=16, MSG_LOG_WIDTH=3)
		(input wire clk, input wire [8*(2**MSG_LOG_WIDTH)-1:0] data, input wire req, output wire uart_tx);
		
		reg [8*(2**MSG_LOG_WIDTH)-1:0] cur_data;
		reg [MSG_LOG_WIDTH-1:0] byte_idx;
		reg busy = 1'b0;
		
		wire [7:0] cur_byte;
		genvar idx;
		generate
			for (idx=0; idx<8; idx=idx+1) begin: byte_sel
				assign cur_byte[idx] = cur_data[8*byte_idx+idx];
			end
		endgenerate
		//assign cur_byte = cur_data[8*byte_idx+7:8*byte_idx];
		
		wire tx_ready;
		uart_transmitter #(.CLK_CYCLES(CLK_CYCLES), .CTR_WIDTH(CTR_WIDTH)) uart_txr(.clk(clk), .data(cur_byte), .req(busy), .ready(tx_ready), .uart_tx(uart_tx));
		
		wire [MSG_LOG_WIDTH-1:0] next_byte_idx;
		assign next_byte_idx = byte_idx + 1'b1;
		
		always @(posedge clk) begin
			if (!busy && req) begin
				busy <= 1;
				cur_data <= data;
				byte_idx <= 0;
			end
			else if (busy && tx_ready) begin
				byte_idx <= next_byte_idx;
				if (next_byte_idx == 0) begin
					busy <= 0;
				end
			end
		end
endmodule

module uart_receiver #(parameter CLK_CYCLES=4178, CTR_WIDTH=16)
	(input wire clk, output reg [7:0] data, output reg received, input wire uart_rx);
		reg [CTR_WIDTH-1:0] ctr = CLK_CYCLES;
		
		reg [4:0] bits_left = 0;
		reg receiving = 0;
		
		always @(posedge clk) begin
			ctr <= ctr - 1'b1;
			received <= 0;
			
			if (ctr == 0) begin
				ctr <= (CLK_CYCLES-1);
				
				data <= {uart_rx, data[7:1]};
				bits_left <= bits_left - 1'b1;
				if (receiving && (bits_left == 1)) begin
					received <= 1;
				end
				if (bits_left == 0) begin
					receiving <= 0;
				end
			end
			
			if (uart_rx == 0 && !receiving) begin
				ctr <= (CLK_CYCLES-1 + CLK_CYCLES / 2); // try to sample in the middle of the bit, to maximize clk rate flexibility.  wait an additional CLK_CYCLES to skip the rest of the start bit
				bits_left <= 4'd8;
				receiving <= 1;
			end
		end
endmodule

module uart_multibyte_receiver #(parameter CLK_CYCLES=4178, CTR_WIDTH=16, MSG_LOG_WIDTH=3)
	(input wire clk, output reg [8*(2**MSG_LOG_WIDTH)-1:0] data, output reg valid, input wire ack, input wire uart_rx, output wire [7:0] led);
		reg [MSG_LOG_WIDTH-1:0] byte_idx;
		wire [MSG_LOG_WIDTH-1:0] next_byte_idx;
		assign next_byte_idx = byte_idx + 1'b1;
		
		reg [8*(2**MSG_LOG_WIDTH)-1:0] buffer;
		wire [8*(2**MSG_LOG_WIDTH)-1:0] next_buffer;
		assign next_buffer = {recvd_byte, buffer[8*(2**MSG_LOG_WIDTH)-1:8]};
		
		wire [7:0] recvd_byte;
		wire recvd_valid;
		uart_receiver #(.CLK_CYCLES(CLK_CYCLES)) uart_rvr(.clk(clk), .data(recvd_byte), .received(recvd_valid), .uart_rx(uart_rx));
				
		always @(posedge clk) begin
			if (ack) valid <= 1'b0;
			
			if (recvd_valid) begin
				buffer <= next_buffer;
				byte_idx <= next_byte_idx;
				if (next_byte_idx == 0) begin
					data <= next_buffer;
					valid <= 1'b1;
				end
			end
		end
endmodule
