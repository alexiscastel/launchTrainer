# LaunchTrainer Lua Script

![Lua script capable remote](doc/files/Remote.jpg "Lua script capable remote")

Welcome to the LaunchTrainer Lua Script repository! This project is a work-in-progress, inspired by my friend Adam's passion for RC glider competitions. The goal of this script will be to help enthusiasts track and optimize their hand-launch performance through detailed and actionable metrics.
What Will LaunchTrainer Do?

LaunchTrainer will be a Lua script designed for RC gliders equipped with Lua script-capable remote controllers. It will capture and analyze various aspects of a hand launch to provide meaningful feedback and insights into your performance.
## Planned Features

The script will offer the following metrics to help you understand and improve your launches:

  - Launch Height: It will measure the peak altitude reached after a launch.
  - Vertical Climb Rate: It will calculate the rate at which your glider ascends during the launch phase.
  - Launch Speed: It will track the speed at which your glider accelerates during the throw.
  - Rotation Distance: It will evaluate the distance traveled while the glider transitions from launch to level flight.

These statistics will be presented in a user-friendly way, with graphical representations and intuitive feedback to make adjustments easier.

![Statistics](doc/files/Curve.jpg "Statistics")

## How Will It Work?

The script will leverage sensor data from your RC glider and remote controller, such as:

  - Altitude Sensors for accurate height tracking.
  - Speed Sensors for monitoring launch velocity.
  - Accelerometers to detect and measure rotational dynamics.

By processing these inputs in real-time, the script will provide instant feedback, making it an invaluable tool for practice and competitions.

