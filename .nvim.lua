RunOptions = {
	file = function(ctx)
		local file = ctx.file
		local cmd = "uv run python " .. file
		ctx.run({ cmd = "echo " .. "'" .. cmd .. "'" .. " && " .. cmd, interactive = true })
	end,
}
vim.cmd("colorscheme vscode")
