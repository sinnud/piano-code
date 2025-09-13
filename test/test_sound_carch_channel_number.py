import pyaudio

def list_output_channels():
    pa = pyaudio.PyAudio()
    print("Available output devices and channel counts:")
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        max_channels = info.get('maxOutputChannels', 0)
        name = info.get('name', 'Unknown')
        if max_channels > 0:
            print(f"Device {i}: {name} - Max Output Channels: {max_channels}")
    pa.terminate()

if __name__ == "__main__":
    list_output_channels()