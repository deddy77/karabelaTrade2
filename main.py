import sys
import argparse
from mt5_helper import connect, shutdown
from strategy import run_strategy
import gui

def main():
    parser = argparse.ArgumentParser(description='KarabelaTrade Bot')
    parser.add_argument('--gui', action='store_true', help='Launch with GUI interface')
    args = parser.parse_args()

    if args.gui:
        # Launch GUI version
        root = gui.tk.Tk()
        app = gui.TradingBotGUI(root)
        root.mainloop()
    else:
        # Command line version
        print("Starting KarabelaTrade Bot...")
        try:
            if connect():
                run_strategy()
            else:
                print("Failed to connect to MetaTrader 5")
        except KeyboardInterrupt:
            print("\nBot stopped by user")
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            shutdown()

if __name__ == "__main__":
    main()
