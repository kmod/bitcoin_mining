`timescale 1ns / 1ps
`default_nettype none
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date:    04:12:55 07/16/2013 
// Design Name: 
// Module Name:    fpga 
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
module fpga(
		input wire input_clk,
		input wire [7:0] sw,
		input wire [4:0] btn,
		output wire [7:0] led,
		output wire [7:0] seg,
		output wire [3:0] an,
		output wire RsTx,
		input wire RsRx
	);

	wire clk; // 10MHz clock
	dcm dcm(.CLK_IN(input_clk), .CLK_OUT(clk)); // 100MHz -> 10MHz DCM

	assign led = sw;
	
	// button synchronizer:
	reg [4:0] btn_sync, btn_sync2;
	always @(posedge clk) begin
		{btn_sync, btn_sync2} <= {btn, btn_sync};
	end
	
	wire [4:0] btn_debounced;
	genvar idx;
	generate
		for (idx=0; idx<5; idx=idx+1) begin: debounce_btn
			debounce btn_db(.clk(clk), .in(btn_sync2[idx]), .out(btn_debounced[idx]));
		end
	endgenerate
	
	reg [4:0] btn_prev;
	
	wire [15:0] sseg_data;
	assign sseg_data = uart_rx_data[15:0];
	sseg #(.N(16)) sseg(.clk(clk), .in(sseg_data), .c(seg), .an(an));
	
	
	/*
	Baud rates:
	@10MHz:
	115,200: 87 cycles
	*/
	
	wire uart_tx_req, uart_tx_ready;
	wire [511:0] uart_tx_data;
	assign uart_tx_data[255:0] = out_hash;
	assign uart_tx_data[263:256] = 8'haa;
	assign uart_tx_data[295:264] = out_nonce;
	assign uart_tx_data[303:296] = 8'haa;
	assign uart_tx_data[511:448] = 64'hdead432987beefaa;
	assign uart_tx_req = (out_hash[255:224+16] == 0);
	uart_multibyte_transmitter #(.CLK_CYCLES(87), .MSG_LOG_WIDTH(6)) uart_mbtx(.clk(clk), .data(uart_tx_data), .req(uart_tx_req), .uart_tx(RsTx));
	
	// Input synchronizer:
	reg RsRx1=1, RsRx2=1;
	always @(posedge clk) begin
		{RsRx1, RsRx2} <= {RsRx, RsRx1};
	end
	wire uart_rx_valid;
	wire [511:0] uart_rx_data;
	wire [255:0] X;
	wire [95:0] Y;
	assign X = uart_rx_data[255:0]; // ex 256'h356d66244c73b9f1e1a328b2c6615412a965a72218c5c19eb5c5d4073db86a04
	assign Y = uart_rx_data[351:256]; // ex 96'h1c2ac4af504e86edec9d69b1
	//assign nonce = uart_rx_data[383:352]; // ex 32'hb2957c02
	
	reg [31:0] in_nonce = 32'hb2957c02;
	wire dsha_accepted;
	
	always @(posedge clk) begin
		if (dsha_accepted) in_nonce <= in_nonce + 1;
	end
	
	uart_multibyte_receiver #(.CLK_CYCLES(87), .MSG_LOG_WIDTH(6)) uart_mbrx(.clk(clk), .data(uart_rx_data), .valid(uart_rx_valid), .ack(1'b0), .uart_rx(RsRx2));
	
	wire [255:0] out_hash;
	wire [31:0] out_nonce;
	dsha_finisher dsha(.clk(clk), .X(X), .Y(Y), .in_nonce(in_nonce), .hash(out_hash), .out_nonce(out_nonce), .accepted(dsha_accepted));
	
	
	
	always @(posedge clk) begin
		btn_prev <= btn_debounced;
	end
endmodule
