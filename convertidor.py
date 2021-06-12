from cx_Freeze import setup, Executable

setup(name = "Robot Trading",
	version = "3.6",
	description = "Par de monedas CHF/JPY",
	executables = [Executable("mind_control_v1_6.py")],)