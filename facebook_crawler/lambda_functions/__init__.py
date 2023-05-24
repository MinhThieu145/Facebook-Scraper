# This is lambda_functions root file to navigate to other lambda functions in the folder

from os.path import dirname, abspath

lambda_functions_root = dirname(abspath(__file__))
print(lambda_functions_root)