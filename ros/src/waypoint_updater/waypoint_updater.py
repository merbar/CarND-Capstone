#!/usr/bin/env python

import rospy
from geometry_msgs.msg import PoseStamped
from styx_msgs.msg import Lane, Waypoint
import numpy as np
import tf
import math

'''
This node will publish waypoints from the car's current position to some `x` distance ahead.

As mentioned in the doc, you should ideally first implement a version which does not care
about traffic lights or obstacles.

Once you have created dbw_node, you will update this node to use the status of traffic lights too.

Please note that our simulator also provides the exact location of traffic lights and their
current status in `/vehicle/traffic_lights` message. You can use this message to build this node
as well as to verify your TL classifier.

TODO (for Yousuf and Aaron): Stopline location for each traffic light.
'''

LOOKAHEAD_WPS = 200 # Number of waypoints we will publish. You can change this number
DEBUG = False

class WaypointUpdater(object):
    def __init__(self):
        self.cur_pose = None
        self.next_waypoints = None

        rospy.init_node('waypoint_updater')

        rospy.Subscriber('/current_pose', PoseStamped, self.pose_cb)
        rospy.Subscriber('/base_waypoints', Lane, self.waypoints_cb)

        # TODO: Add a subscriber for /traffic_waypoint and /obstacle_waypoint below
        self.final_waypoints_pub = rospy.Publisher('final_waypoints', Lane, queue_size=1)
        # TODO: Add other member variables you need below

        rospy.spin()

    def pose_cb(self, msg):
        # TODO: Implement
        self.cur_pose = msg

    def waypoints_cb(self, waypoints):
        # TODO: Implement
        if self.cur_pose is not None:
            wp_base_size = len(waypoints.waypoints)
            # rospy.loginfo('wp_base_size: {}'.format(wp_base_size)) # 10902 wps at start
            next_wp_i = self.next_waypoint(self.cur_pose.pose, waypoints.waypoints)
            next_waypoints = waypoints.waypoints[next_wp_i:next_wp_i+LOOKAHEAD_WPS]

            # publish
            final_waypoints_msg = Lane()
            final_waypoints_msg.header.frame_id = '/world'
            final_waypoints_msg.header.stamp = rospy.Time(0)
            final_waypoints_msg.waypoints = waypoints.waypoints[next_wp_i:next_wp_i+LOOKAHEAD_WPS]
            self.final_waypoints_pub.publish(final_waypoints_msg)

    def traffic_cb(self, msg):
        # TODO: Callback for /traffic_waypoint message. Implement
        pass

    def obstacle_cb(self, msg):
        # TODO: Callback for /obstacle_waypoint message. We will implement it later
        pass

    def get_waypoint_velocity(self, waypoint):
        return waypoint.twist.twist.linear.x

    def set_waypoint_velocity(self, waypoints, waypoint, velocity):
        waypoints[waypoint].twist.twist.linear.x = velocity

    def distance(self, waypoints, wp1, wp2):
        dist = 0
        dl = lambda a, b: math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2  + (a.z-b.z)**2)
        for i in range(wp1, wp2+1):
            dist += dl(waypoints[wp1].pose.pose.position, waypoints[i].pose.pose.position)
            wp1 = i
        return dist

    def closest_waypoint(self, pose, waypoints):
        closest_len = 100000
        closest_wp_i = 0
        dl = lambda a, b: math.sqrt((a.x-b.x)**2 + (a.y-b.y)**2  + (a.z-b.z)**2)
        for i in range(len(waypoints)):
            dist = dl(pose.position, waypoints[i].pose.pose.position)
            if (dist < closest_len):
                closest_len = dist
                closest_wp_i = i
        return closest_wp_i

    def next_waypoint(self, pose, waypoints):
        closest_wp_i = self.closest_waypoint(pose, waypoints)
        map_x = waypoints[closest_wp_i].pose.pose.position.x
        map_y = waypoints[closest_wp_i].pose.pose.position.y
        
        heading = math.atan2((map_y - pose.position.y), (map_x - pose.position.x))

        pose_quaternion = (pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w)
        (_, _, yaw) = tf.transformations.euler_from_quaternion(pose_quaternion)
        angle = math.fabs(heading - yaw)
        
        if DEBUG:
            rospy.logerr('current_pose - x:{}, y:{},z:{}'.format(pose.position.x, pose.position.y, pose.position.z))
            rospy.logerr('ego yaw: {}'.format(yaw))
            rospy.logerr('heading: {}, angle: {}'.format(heading, angle))
            rospy.logerr('closest wp: {}; {}-{}'.format(closest_wp_i, waypoints[closest_wp_i].pose.pose.position.x, waypoints[closest_wp_i].pose.pose.position.y))

        if angle > (math.pi / 4):
            closest_wp_i += 1
            if DEBUG:
                rospy.logerr('corrected wp: {}; {}-{}'.format(closest_wp_i, waypoints[closest_wp_i].pose.pose.position.x, waypoints[closest_wp_i].pose.pose.position.y))

        if DEBUG:
            rospy.logerr(' ')
        
        return closest_wp_i

if __name__ == '__main__':
    try:
        WaypointUpdater()
    except rospy.ROSInterruptException:
        rospy.logerr('Could not start waypoint updater node.')

