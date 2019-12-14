class InputFileNotFoundError(FileNotFoundError):
	def __init__(self, path):
		from os.path import basename
		self.path = path
		super().__init__(f"Cannot open file {basename(path)}\nMake sure to execute 'sudo ./generate_files.sh' first!")

	def get_path(self):
		return self.path
