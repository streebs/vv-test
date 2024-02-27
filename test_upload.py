from visualvault import VV

def main():
    vault = VV()

    # Test 1
    vault.upload_document("Student Records/DevTest", "test.txt", "test_folder/test.txt")
    # Test 2
    vault.upload_document("Student Records/DevTest", "test2.txt", "test_folder/test2.txt")
    # Test 3
    vault.upload_document("Student Records/DevTest", "test3.txt", "test_folder/test3.txt")

if __name__ == '__main__':
    main()