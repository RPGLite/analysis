# William Kavanagh, June 2020

from helper_fns import *
import numpy as np
import matplotlib.pyplot as plt
import math
from bson import objectid
import pymongo

# TUNEABLE
elo_delta = 10
skill_delta = 1
luck_delta = 1
total_cost_delta = 0.01
optimality_delta = 0.005
mistake_threshold = 0.05
major_mistake_threshold = 0.25

beta_optimality = [
    [0.5, 0.5219, 0.5048, 0.4234, 0.389, 0.4148, 0.4626, 0.6031, 0.6107, 0.3839, 0.4375, 0.4183, 0.5543, 0.4445, 0.4806, 0.3239, 0.4793, 0.4277, 0.4369, 0.3203, 0.4048, 0.472, 0.3372, 0.3535, 0.3614, 0.3009, 0.3509, 0.3416],
    [0.4781, 0.5, 0.4926, 0.3857, 0.419, 0.4352, 0.435, 0.5766, 0.585, 0.448, 0.4904, 0.481, 0.5765, 0.492, 0.5216, 0.3419, 0.521, 0.4639, 0.4849, 0.3881, 0.4486, 0.5085, 0.4639, 0.3573, 0.4335, 0.3714, 0.4184, 0.389],
    [0.4952, 0.5074, 0.5, 0.3989, 0.4523, 0.3333, 0.4629, 0.583, 0.5927, 0.4697, 0.5273, 0.4045, 0.5766, 0.5145, 0.6118, 0.407, 0.4598, 0.4904, 0.5104, 0.4563, 0.4274, 0.5481, 0.4681, 0.3497, 0.4608, 0.3891, 0.486, 0.3707],
    [0.5766, 0.6143, 0.6011, 0.5, 0.4634, 0.4573, 0.5493, 0.6839, 0.6547, 0.5046, 0.5058, 0.4741, 0.6396, 0.6273, 0.6793, 0.3702, 0.5767, 0.4244, 0.6063, 0.408, 0.5557, 0.5428, 0.4776, 0.4201, 0.481, 0.3756, 0.3588, 0.4058],
    [0.611, 0.581, 0.5477, 0.5366, 0.5, 0.4793, 0.5361, 0.6494, 0.6175, 0.6109, 0.5717, 0.5377, 0.6256, 0.4582, 0.6269, 0.4527, 0.4747, 0.4906, 0.5409, 0.4519, 0.4949, 0.5458, 0.5083, 0.4933, 0.4969, 0.4312, 0.4741, 0.4366],
    [0.5852, 0.5648, 0.6667, 0.5427, 0.5207, 0.5, 0.6392, 0.6544, 0.6741, 0.552, 0.6011, 0.5177, 0.6474, 0.4605, 0.7031, 0.4247, 0.5126, 0.5329, 0.5876, 0.4192, 0.645, 0.5993, 0.5721, 0.4614, 0.5291, 0.4508, 0.5333, 0.474],
    [0.5374, 0.565, 0.5371, 0.4507, 0.4639, 0.3608, 0.5, 0.6615, 0.6797, 0.5226, 0.57, 0.4653, 0.6641, 0.5827, 0.5911, 0.4217, 0.507, 0.5585, 0.5697, 0.476, 0.4566, 0.6058, 0.5291, 0.4228, 0.5058, 0.3981, 0.5071, 0.4007],
    [0.3969, 0.4234, 0.417, 0.3161, 0.3506, 0.3456, 0.3385, 0.5, 0.4817, 0.2356, 0.3422, 0.3289, 0.4647, 0.38, 0.3087, 0.3018, 0.4147, 0.3136, 0.3044, 0.2759, 0.3065, 0.3531, 0.2635, 0.2556, 0.2671, 0.2576, 0.3178, 0.2844],
    [0.3893, 0.415, 0.4073, 0.3453, 0.3825, 0.3259, 0.3203, 0.5183, 0.5, 0.2507, 0.4529, 0.3007, 0.4728, 0.3489, 0.3234, 0.3856, 0.3778, 0.3264, 0.3154, 0.3398, 0.278, 0.3458, 0.289, 0.286, 0.2777, 0.3072, 0.3857, 0.2653],
    [0.6161, 0.552, 0.5303, 0.4954, 0.3891, 0.448, 0.4774, 0.7644, 0.7493, 0.5, 0.4476, 0.4814, 0.698, 0.5015, 0.5247, 0.2691, 0.5026, 0.3418, 0.4842, 0.3236, 0.4711, 0.4135, 0.3402, 0.3234, 0.3516, 0.2811, 0.3281, 0.3178],
    [0.5625, 0.5096, 0.4727, 0.4942, 0.4283, 0.3989, 0.43, 0.6578, 0.5471, 0.5524, 0.5, 0.493, 0.5549, 0.3535, 0.5006, 0.4248, 0.4291, 0.4329, 0.4019, 0.3532, 0.413, 0.4988, 0.3711, 0.4345, 0.3974, 0.3624, 0.3922, 0.401],
    [0.5817, 0.519, 0.5955, 0.5259, 0.4623, 0.4823, 0.5347, 0.6711, 0.6993, 0.5186, 0.507, 0.5, 0.6185, 0.344, 0.5625, 0.3369, 0.4755, 0.4062, 0.51, 0.3633, 0.5589, 0.5397, 0.4083, 0.3891, 0.4562, 0.3427, 0.4567, 0.4091],
    [0.4457, 0.4235, 0.4234, 0.3604, 0.3744, 0.3526, 0.3359, 0.5353, 0.5272, 0.302, 0.4451, 0.3815, 0.5, 0.3532, 0.3619, 0.3216, 0.4818, 0.3418, 0.3786, 0.3178, 0.3147, 0.3715, 0.3319, 0.3195, 0.2942, 0.31, 0.3679, 0.2899],
    [0.5555, 0.508, 0.4855, 0.3727, 0.5418, 0.5395, 0.4173, 0.62, 0.6511, 0.4985, 0.6465, 0.656, 0.6468, 0.5, 0.5877, 0.5042, 0.6029, 0.4243, 0.5361, 0.5054, 0.5749, 0.4468, 0.5613, 0.3637, 0.4858, 0.6113, 0.5151, 0.5098],
    [0.5194, 0.4784, 0.3882, 0.3207, 0.3731, 0.2969, 0.4089, 0.6913, 0.6766, 0.4753, 0.4994, 0.4375, 0.6381, 0.4123, 0.5, 0.2614, 0.423, 0.2169, 0.3953, 0.3043, 0.3666, 0.3378, 0.3799, 0.221, 0.2559, 0.2919, 0.1858, 0.2248],
    [0.6761, 0.6581, 0.593, 0.6298, 0.5473, 0.5753, 0.5783, 0.6982, 0.6144, 0.7309, 0.5752, 0.6631, 0.6784, 0.4958, 0.7386, 0.5, 0.6974, 0.5068, 0.6122, 0.3965, 0.6307, 0.531, 0.5718, 0.6232, 0.6201, 0.5578, 0.4463, 0.6029],
    [0.5207, 0.479, 0.5402, 0.4233, 0.5253, 0.4874, 0.493, 0.5853, 0.6222, 0.4974, 0.5709, 0.5245, 0.5182, 0.3971, 0.577, 0.3026, 0.5, 0.3868, 0.5758, 0.4408, 0.6441, 0.4749, 0.5145, 0.3803, 0.4454, 0.4845, 0.4631, 0.4553],
    [0.5723, 0.5361, 0.5096, 0.5756, 0.5094, 0.4671, 0.4415, 0.6864, 0.6736, 0.6582, 0.5671, 0.5938, 0.6582, 0.5757, 0.7831, 0.4932, 0.6132, 0.5, 0.696, 0.4203, 0.5326, 0.5017, 0.6129, 0.5474, 0.654, 0.4714, 0.4726, 0.4624],
    [0.5631, 0.5151, 0.4896, 0.3937, 0.4591, 0.4124, 0.4303, 0.6956, 0.6846, 0.5158, 0.5981, 0.49, 0.6214, 0.4639, 0.6047, 0.3878, 0.4242, 0.304, 0.5, 0.3919, 0.4647, 0.4291, 0.4594, 0.2885, 0.4031, 0.3662, 0.3543, 0.3107],
    [0.6797, 0.6119, 0.5437, 0.592, 0.5481, 0.5808, 0.524, 0.7241, 0.6602, 0.6764, 0.6468, 0.6367, 0.6822, 0.4946, 0.6957, 0.6035, 0.5592, 0.5797, 0.6081, 0.5, 0.6238, 0.5425, 0.59, 0.5868, 0.5709, 0.5574, 0.5382, 0.5864],
    [0.5952, 0.5514, 0.5726, 0.4443, 0.5051, 0.355, 0.5434, 0.6935, 0.722, 0.5289, 0.587, 0.4411, 0.6853, 0.4251, 0.6334, 0.3693, 0.3559, 0.4674, 0.5353, 0.3762, 0.5, 0.5472, 0.5513, 0.3339, 0.4719, 0.3041, 0.4623, 0.3678],
    [0.528, 0.4915, 0.4519, 0.4572, 0.4542, 0.4007, 0.3942, 0.6469, 0.6542, 0.5865, 0.5012, 0.4603, 0.6285, 0.5532, 0.6622, 0.469, 0.5251, 0.4983, 0.5709, 0.4575, 0.4528, 0.5, 0.5065, 0.4366, 0.5063, 0.4057, 0.509, 0.3903],
    [0.6628, 0.5361, 0.5319, 0.5224, 0.4917, 0.4279, 0.4709, 0.7365, 0.711, 0.6598, 0.6289, 0.5917, 0.6681, 0.4387, 0.6201, 0.4282, 0.4855, 0.3871, 0.5406, 0.41, 0.4487, 0.4935, 0.5, 0.4818, 0.4817, 0.4188, 0.3806, 0.395],
    [0.6465, 0.6427, 0.6503, 0.5799, 0.5067, 0.5386, 0.5772, 0.7444, 0.714, 0.6766, 0.5655, 0.6109, 0.6805, 0.6363, 0.779, 0.3768, 0.6197, 0.4526, 0.7115, 0.4132, 0.6661, 0.5634, 0.5182, 0.5, 0.5794, 0.4298, 0.3813, 0.4166],
    [0.6386, 0.5665, 0.5392, 0.519, 0.5031, 0.4709, 0.4942, 0.7329, 0.7223, 0.6484, 0.6026, 0.5438, 0.7058, 0.5142, 0.7441, 0.3799, 0.5546, 0.346, 0.5969, 0.4291, 0.5281, 0.4937, 0.5183, 0.4206, 0.5, 0.4187, 0.3778, 0.39],
    [0.6991, 0.6286, 0.6109, 0.6244, 0.5688, 0.5492, 0.6019, 0.7424, 0.6928, 0.7189, 0.6376, 0.6573, 0.69, 0.3887, 0.7081, 0.4422, 0.5155, 0.5286, 0.6338, 0.4426, 0.6959, 0.5943, 0.5812, 0.5702, 0.5813, 0.5, 0.5122, 0.5077],
    [0.6491, 0.5816, 0.514, 0.6412, 0.5259, 0.4667, 0.4929, 0.6822, 0.6143, 0.6719, 0.6078, 0.5433, 0.6321, 0.4849, 0.8142, 0.5537, 0.5369, 0.5274, 0.6457, 0.4618, 0.5377, 0.491, 0.6194, 0.6187, 0.6222, 0.4878, 0.5, 0.4511],
    [0.6584, 0.611, 0.6293, 0.5942, 0.5634, 0.526, 0.5993, 0.7156, 0.7347, 0.6822, 0.599, 0.5909, 0.7101, 0.4902, 0.7752, 0.3971, 0.5447, 0.5376, 0.6893, 0.4136, 0.6322, 0.6097, 0.605, 0.5834, 0.61, 0.4923, 0.5489, 0.5]
    ]

tango_optimality = [
    [0.5, 0.6552, 0.7224, 0.5131, 0.5547, 0.5311, 0.4846, 0.692, 0.6191, 0.5253, 0.5593, 0.5183, 0.6239, 0.6057, 0.4541, 0.5052, 0.6168, 0.5109, 0.5348, 0.5461, 0.6402, 0.5018, 0.5076, 0.4618, 0.4895, 0.5409, 0.5749, 0.4995],
    [0.3448, 0.5, 0.4712, 0.2989, 0.4873, 0.4572, 0.3865, 0.5062, 0.508, 0.3169, 0.5271, 0.5125, 0.4931, 0.4025, 0.4773, 0.3952, 0.6188, 0.3473, 0.4055, 0.4636, 0.5952, 0.4119, 0.5285, 0.4285, 0.36, 0.6223, 0.4232, 0.5291],
    [0.2776, 0.5288, 0.5, 0.354, 0.4497, 0.4802, 0.416, 0.505, 0.5065, 0.2991, 0.4827, 0.3892, 0.4814, 0.4891, 0.529, 0.4572, 0.621, 0.4585, 0.4698, 0.4823, 0.594, 0.523, 0.5541, 0.4743, 0.3974, 0.5794, 0.4652, 0.5144],
    [0.4869, 0.7011, 0.646, 0.5, 0.5525, 0.6062, 0.4953, 0.6607, 0.6512, 0.4991, 0.6184, 0.5029, 0.5976, 0.6189, 0.6701, 0.4851, 0.6529, 0.4936, 0.6123, 0.5295, 0.6259, 0.5336, 0.581, 0.4859, 0.5128, 0.5498, 0.518, 0.4309],
    [0.4453, 0.5127, 0.5503, 0.4475, 0.5, 0.5476, 0.4088, 0.5451, 0.5269, 0.4935, 0.5751, 0.4791, 0.5258, 0.354, 0.5539, 0.4632, 0.5457, 0.4239, 0.4436, 0.4642, 0.5655, 0.4837, 0.5173, 0.4828, 0.4358, 0.5425, 0.4747, 0.4646],
    [0.4689, 0.5428, 0.5198, 0.3938, 0.4524, 0.5, 0.4358, 0.5752, 0.5255, 0.4509, 0.4789, 0.4912, 0.5683, 0.5301, 0.6706, 0.4442, 0.6187, 0.5325, 0.4229, 0.425, 0.6339, 0.3681, 0.5363, 0.4634, 0.4595, 0.4892, 0.4651, 0.4329],
    [0.5154, 0.6135, 0.584, 0.5047, 0.5912, 0.5642, 0.5, 0.5385, 0.5475, 0.3788, 0.5771, 0.4911, 0.5301, 0.5177, 0.6179, 0.5054, 0.6707, 0.4785, 0.5415, 0.543, 0.615, 0.5484, 0.5831, 0.5627, 0.4924, 0.6219, 0.5527, 0.536],
    [0.308, 0.4938, 0.495, 0.3393, 0.4549, 0.4248, 0.4615, 0.5, 0.4643, 0.3304, 0.3831, 0.2866, 0.447, 0.411, 0.2367, 0.3997, 0.4707, 0.3435, 0.386, 0.4509, 0.4476, 0.4113, 0.3525, 0.3279, 0.353, 0.3894, 0.4819, 0.3204],
    [0.3809, 0.492, 0.4935, 0.3488, 0.4731, 0.4745, 0.4525, 0.5357, 0.5, 0.3868, 0.5096, 0.4639, 0.5004, 0.373, 0.2705, 0.4527, 0.4871, 0.3421, 0.3813, 0.4759, 0.4528, 0.4172, 0.3817, 0.3265, 0.3547, 0.4785, 0.4925, 0.3435],
    [0.4747, 0.6831, 0.7009, 0.5009, 0.5065, 0.5491, 0.6212, 0.6696, 0.6132, 0.5, 0.4824, 0.3874, 0.6028, 0.6284, 0.4401, 0.4483, 0.5899, 0.5263, 0.5235, 0.4895, 0.5799, 0.5985, 0.4554, 0.4438, 0.4627, 0.4298, 0.5109, 0.4471],
    [0.4407, 0.4729, 0.5173, 0.3816, 0.4249, 0.5211, 0.4229, 0.6169, 0.4904, 0.5176, 0.5, 0.437, 0.496, 0.3755, 0.4073, 0.4023, 0.4378, 0.4159, 0.341, 0.4176, 0.4784, 0.4581, 0.4015, 0.3744, 0.383, 0.4227, 0.4527, 0.3898],
    [0.4817, 0.4875, 0.6108, 0.4971, 0.5209, 0.5088, 0.5089, 0.7134, 0.5361, 0.6126, 0.563, 0.5, 0.6282, 0.5411, 0.541, 0.4617, 0.5585, 0.4473, 0.4316, 0.4613, 0.689, 0.4093, 0.4779, 0.3965, 0.493, 0.5031, 0.5438, 0.472],
    [0.3761, 0.5069, 0.5186, 0.4024, 0.4742, 0.4317, 0.4699, 0.553, 0.4996, 0.3972, 0.504, 0.3718, 0.5, 0.4631, 0.3232, 0.4276, 0.5033, 0.3971, 0.4246, 0.4692, 0.4611, 0.4616, 0.4524, 0.3714, 0.3801, 0.4637, 0.4995, 0.3634],
    [0.3943, 0.5975, 0.5109, 0.3811, 0.646, 0.4699, 0.4823, 0.589, 0.627, 0.3716, 0.6245, 0.4589, 0.5369, 0.5, 0.5226, 0.5385, 0.6126, 0.4334, 0.5273, 0.5476, 0.548, 0.4615, 0.5913, 0.4549, 0.4835, 0.6551, 0.5443, 0.469],
    [0.5459, 0.5227, 0.471, 0.3299, 0.4461, 0.3294, 0.3821, 0.7633, 0.7295, 0.5599, 0.5927, 0.459, 0.6768, 0.4774, 0.5, 0.4067, 0.5415, 0.3228, 0.3744, 0.3973, 0.4827, 0.3893, 0.4602, 0.3308, 0.282, 0.4352, 0.3566, 0.332],
    [0.4948, 0.6048, 0.5428, 0.5149, 0.5368, 0.5558, 0.4946, 0.6003, 0.5473, 0.5517, 0.5977, 0.5383, 0.5724, 0.4615, 0.5933, 0.5, 0.6389, 0.4375, 0.4902, 0.4122, 0.5827, 0.4613, 0.5453, 0.5664, 0.5035, 0.5942, 0.4592, 0.5176],
    [0.3832, 0.3812, 0.379, 0.3471, 0.4543, 0.3813, 0.3293, 0.5293, 0.5129, 0.4101, 0.5622, 0.4415, 0.4967, 0.3874, 0.4585, 0.3611, 0.5, 0.3334, 0.4948, 0.4431, 0.5101, 0.347, 0.559, 0.3824, 0.4186, 0.5322, 0.428, 0.4406],
    [0.4891, 0.6527, 0.5415, 0.5064, 0.5761, 0.4675, 0.5215, 0.6565, 0.6579, 0.4737, 0.5841, 0.5527, 0.6029, 0.5666, 0.6772, 0.5625, 0.6666, 0.5, 0.6336, 0.5197, 0.5964, 0.5106, 0.6546, 0.5428, 0.564, 0.6074, 0.5628, 0.5283],
    [0.4652, 0.5945, 0.5302, 0.3877, 0.5564, 0.5771, 0.4585, 0.614, 0.6187, 0.4765, 0.659, 0.5684, 0.5754, 0.4727, 0.6256, 0.5098, 0.5052, 0.3664, 0.5, 0.4764, 0.5172, 0.4136, 0.5349, 0.4166, 0.4242, 0.4802, 0.4764, 0.3686],
    [0.4539, 0.5364, 0.5177, 0.4705, 0.5358, 0.575, 0.457, 0.5491, 0.5241, 0.5105, 0.5824, 0.5387, 0.5308, 0.4524, 0.6027, 0.5878, 0.5569, 0.4803, 0.5236, 0.5, 0.5927, 0.4633, 0.5778, 0.5423, 0.5037, 0.5912, 0.5213, 0.5331],
    [0.3598, 0.4048, 0.406, 0.3741, 0.4345, 0.3661, 0.385, 0.5524, 0.5472, 0.4201, 0.5216, 0.311, 0.5389, 0.452, 0.5173, 0.4173, 0.4899, 0.4036, 0.4828, 0.4073, 0.5, 0.4412, 0.5948, 0.395, 0.431, 0.4759, 0.4538, 0.416],
    [0.4982, 0.5881, 0.477, 0.4664, 0.5163, 0.6319, 0.4516, 0.5887, 0.5828, 0.4015, 0.5419, 0.5907, 0.5384, 0.5385, 0.6107, 0.5387, 0.653, 0.4894, 0.5864, 0.5367, 0.5588, 0.5, 0.5789, 0.5157, 0.5377, 0.5738, 0.5704, 0.5044],
    [0.4924, 0.4715, 0.4459, 0.419, 0.4827, 0.4637, 0.4169, 0.6475, 0.6183, 0.5446, 0.5985, 0.5221, 0.5476, 0.4087, 0.5398, 0.4547, 0.441, 0.3454, 0.4651, 0.4222, 0.4052, 0.4211, 0.5, 0.4341, 0.4174, 0.4364, 0.4229, 0.3542],
    [0.5382, 0.5715, 0.5257, 0.5141, 0.5172, 0.5366, 0.4373, 0.6721, 0.6735, 0.5562, 0.6256, 0.6035, 0.6286, 0.5451, 0.6692, 0.4336, 0.6176, 0.4572, 0.5834, 0.4577, 0.605, 0.4843, 0.5659, 0.5, 0.5015, 0.5235, 0.4781, 0.4791],
    [0.5105, 0.64, 0.6026, 0.4872, 0.5642, 0.5405, 0.5076, 0.647, 0.6453, 0.5373, 0.617, 0.507, 0.6199, 0.5165, 0.718, 0.4965, 0.5814, 0.436, 0.5758, 0.4963, 0.569, 0.4623, 0.5826, 0.4985, 0.5, 0.5101, 0.4836, 0.4086],
    [0.4591, 0.3777, 0.4206, 0.4502, 0.4575, 0.5108, 0.3781, 0.6106, 0.5215, 0.5702, 0.5773, 0.4969, 0.5363, 0.3449, 0.5648, 0.4058, 0.4678, 0.3926, 0.5198, 0.4088, 0.5241, 0.4262, 0.5636, 0.4765, 0.4899, 0.5, 0.4669, 0.4561],
    [0.4251, 0.5768, 0.5348, 0.482, 0.5253, 0.5349, 0.4473, 0.5181, 0.5075, 0.4891, 0.5473, 0.4562, 0.5005, 0.4557, 0.6434, 0.5408, 0.572, 0.4372, 0.5236, 0.4787, 0.5462, 0.4296, 0.5771, 0.5219, 0.5164, 0.5331, 0.5, 0.4353],
    [0.5005, 0.4709, 0.4856, 0.5691, 0.5354, 0.5671, 0.464, 0.6796, 0.6565, 0.5529, 0.6102, 0.528, 0.6366, 0.531, 0.668, 0.4824, 0.5594, 0.4717, 0.6314, 0.4669, 0.584, 0.4956, 0.6458, 0.5209, 0.5914, 0.5439, 0.5647, 0.5]
    ]

s1data = process_lookup("beta")
s2data = process_lookup("tango-2-3")       

def flip_state(s):
    return [1] + s[10:] + s[1:10]

total_games = db.completed_games.count_documents({"winner":{"$exists":True}, "balance_code":{"$exists":False}}) - 1 # dodgy game.
won_by_first = 0                # amount won by player going first
won_by_higher_skill = 0         # amount won by player with significantly higher skill (>skill_delta above at end) [0.5 if skill is within delta]
equivalent_skill = 0            # similar skill level
won_by_experience = 0           # amount won by player to have played more games
equivalent_experience = 0       # same games played
won_by_higher_elo = 0           # amount won by player with significantly higher elo (>elo_delta more at end) [0.5 if elo is within delta]
equivalent_elo = 0              # similar elo ratings
won_by_lower_cost = 0           # amount won by player with lower average cost/move
equivalent_cost = 0             # equivalent costs
won_by_fewer_mistakes = 0       # amount won by player with fewer mistakes (moves with cost/optimal > mistake_threshold)
equivalent_mistakes = 0         # games with equivalent mistakes
won_by_selection = 0            # amount won by player with material that should win if players are playing optimally
equivalent_selection = 0        # similar materials
won_by_luck = 0                 # amount won by player with significantly higher roll results (>luck_delta more at end) [0.5 if luck is within delta]
equivalent_luck = 0             # similar roll fortune
won_by_first_miss = 0           # amount won by the player who didn't miss first        
won_by_miss_count = 0           # amount won by the player who won less
equivalent_misses = 0
no_misses = 0                   
won_by_first_mistake = 0        # amount won by the player who didn't make the first mistake
no_mistakes = 0
won_by_total_cost = 0           # amount won by the player with the highest total cost
equivalent_cumulative_cost = 0  
won_by_first_kill = 0           # amount won by the player that first killed an opposing character
won_by_fewer_major_mistakes = 0 # amount won by the player to make fewer major mistakes
no_major_mistakes = 0
won_by_first_major_mistake = 0  # amount own by player who did not make the first major mistake
equivalent_major_mistakes = 0   # same number of major errors made


players_seen = []               # list of players seen. Used to calculate prior games played quickly

# Process S1 games
set_config("beta")
for g in db.completed_games.find({"winner":{"$exists":True}, "balance_code":{"$exists":False}}).sort("start_date", pymongo.ASCENDING):
    p1_rolls = []
    p2_rolls = []
    p1_costs = []
    p2_costs = []
    p1_mistakes = 0
    p2_mistakes = 0
    p1_major_mistakes = 0
    p2_major_mistakes = 0
    p1_misses = 0
    p2_misses = 0
    first_death = 0
    first_miss = 0
    first_mistake = 0
    first_major_mistake = 0

    if g["_id"] == objectid.ObjectId("5e98b4658a225cfc82573fd1"):    # Ignore dodgy game.
        continue

    # Who went first and did they win?
    if g["Moves"][0][1] == str(g["winner"]):
        won_by_first += 1

    # who has played more games and did they win?
    p1_played = players_seen.count(g["usernames"][0])
    p2_played = players_seen.count(g["usernames"][1])
    players_seen += g["usernames"]
    if (p1_played > p2_played and g["winner"] == 1) or (p1_played < p2_played and g["winner"] == 2):
        won_by_experience += 1
    if p1_played == p2_played:
        equivalent_experience += 1

    # What material was used and which should win?
    pair1 = g["p1c1"][0] + g["p1c2"][0]
    pair2 = g["p2c1"][0] + g["p2c2"][0]
    if chars.index(pair1[0]) > chars.index(pair1[1]):
        pair1 = pair1[1]+pair1[0]
    if chars.index(pair2[0]) > chars.index(pair2[1]):
        pair2 = pair2[1]+pair2[0]

    if abs(beta_optimality[pairs.index(pair1)][pairs.index(pair2)] - 0.5) < optimality_delta:
        equivalent_selection += 1
    elif (g["winner"] == 1 and beta_optimality[pairs.index(pair1)][pairs.index(pair2)] > 0.5) or (g["winner"] == 2 and beta_optimality[pairs.index(pair1)][pairs.index(pair2)] < 0.5):
        won_by_selection += 1



    state = get_initial_state(g)
    for m in g["Moves"]:     # for every move made
        
        if first_death == 0:
            if state[1:9].count(0) > 6:
                first_death = 1
            elif state[10:18].count(0) > 6:
                first_death = 2

        if first_miss == 0 and was_a_miss(m, state):
            first_miss = int(m[1])

        # add the roll to the arrays
        rolls_in_move = []
        if m.count("_") == 1:
            if "skip" not in m:
                rolls_in_move += [int(m.split("_")[1])]
        else:
            rolls_in_move += [int(m.split("_")[2])]   # add second roll
            rolls_in_move += [int(m.split("_")[1].split("p")[0])]
        if m[1] == "1":
           p1_rolls += rolls_in_move
        else:
            p2_rolls += rolls_in_move 
        # add the costs to the arrays and update mistake count
        if m[1] == "1":
            if was_a_miss(m, state):
                p1_misses += 1                        
            p1_costs += [cost(state, pair1, m, s1data)]
            val, pos = cost(state, pair1, m, s1data, classify_mistake=True)
            if pos > 0:
                if (pos-val) / pos >= mistake_threshold:
                    p1_mistakes += 1
                    if first_mistake == 0:
                        first_mistake = 1
                if (pos-val) / pos >= major_mistake_threshold:
                    p1_major_mistakes += 1
                    if first_major_mistake == 0:
                        first_major_mistake = 1
        elif m[1] == "2":
            if was_a_miss(m, state):
                p2_misses += 1
            p2_costs += [cost(flip_state(state), pair2, m, s1data)]
            val, pos = cost(flip_state(state), pair2, m, s1data, classify_mistake=True)
            if pos > 0:
                if (pos-val) / pos >= mistake_threshold:
                    p2_mistakes += 1
                    if first_mistake == 0:
                        first_mistake = 2
                    if (pos-val) / pos >= major_mistake_threshold:
                        p2_major_mistakes += 1
                        if first_major_mistake == 0:
                            first_major_mistake = 2
        do_action(m, state)

    # luck check
    if len(p1_rolls) == 0:
        p1_rolls = [0]
    if len(p2_rolls) == 0:
        p2_rolls = [0]
    if np.average(p1_rolls) - np.average(p2_rolls) < luck_delta:
        # luck was similar enough to discount
        equivalent_luck += 1
    elif (g["winner"] == 1 and np.average(p1_rolls) > np.average(p2_rolls)) or (g["winner"] == 2 and np.average(p1_rolls) < np.average(p2_rolls)):
        won_by_luck += 1
    
    # skill check
    if len(g["skill_points_at_end"]) != 2:
        equivalent_skill += 1
    elif g["skill_points_at_end"][g["usernames"][0]] - g["skill_points_at_end"][g["usernames"][1]] < skill_delta:
        equivalent_skill += 1
    elif g["skill_points_at_end"][g["usernames"][0]] > g["skill_points_at_end"][g["usernames"][1]] and g["winner"] == 1:
        won_by_higher_skill += 1
    elif g["skill_points_at_end"][g["usernames"][0]] < g["skill_points_at_end"][g["usernames"][1]] and g["winner"] == 2:
        won_by_higher_skill += 1
    
    # Elo check
    if g["elo_scores_at_end"][g["usernames"][0]] - g["elo_scores_at_end"][g["usernames"][1]] < elo_delta:
        equivalent_elo += 1
    elif g["elo_scores_at_end"][g["usernames"][0]] > g["elo_scores_at_end"][g["usernames"][1]] and g["winner"] == 1:
        won_by_higher_elo += 1
    elif g["elo_scores_at_end"][g["usernames"][0]] < g["elo_scores_at_end"][g["usernames"][1]] and g["winner"] == 2:
        won_by_higher_elo += 1
    
    # average cost check
    if len(p1_costs) == 0 or len(p2_costs) == 0:
        equivalent_cost += 1 # no moves made by a player. Possible with M
    elif (np.average(p1_costs) < np.average(p2_costs) and g["winner"] == 1) or (np.average(p1_costs) > np.average(p2_costs) and g["winner"] == 2):
        won_by_lower_cost += 1
    elif np.average(p1_costs) == np.average(p2_costs):
        equivalent_cost += 1

    # total cost check
    if abs(sum(p1_costs) - sum(p2_costs)) < total_cost_delta:
        equivalent_cumulative_cost += 1
    elif (g["winner"] == 1 and sum(p1_costs) < sum(p2_costs)) or (g["winner"] == 2 and sum(p1_costs) > sum(p2_costs)):
        won_by_total_cost += 1

    # mistake check
    if (g["winner"] == 1 and p1_mistakes < p2_mistakes) or (g["winner"] == 2 and p1_mistakes > p2_mistakes):
        won_by_fewer_mistakes += 1
    if p1_mistakes == p2_mistakes:
        equivalent_mistakes += 1

    # first miss check
    if first_miss == 0:
        no_misses += 1
    elif first_miss != g["winner"]:
        won_by_first_miss += 1

    # first mistake check
    if first_mistake == 0:
        no_mistakes += 1
    elif first_mistake != g["winner"]:
        won_by_first_mistake += 1

    # misses check
    if p1_misses == p2_misses:
        equivalent_misses += 1
    elif (g["winner"] == 1 and p1_misses < p2_misses) or (g["winner"] == 2 and p1_misses > p2_misses):
        won_by_miss_count += 1

    # first kill check
    if first_miss != g["winner"] and first_death != 0:
        won_by_first_kill += 1

    # first major mistake check
    if first_major_mistake != g["winner"] and first_major_mistake != 0:
        won_by_first_major_mistake += 1
    
    # major mistake count check
    if (p1_major_mistakes > p2_major_mistakes and g["winner"] == 2) or (p1_major_mistakes < p2_major_mistakes and g["winner"] == 1):
        won_by_fewer_major_mistakes += 1
    if first_major_mistake == 0:
        no_major_mistakes += 1
    elif p1_major_mistakes == p2_major_mistakes:
        equivalent_major_mistakes += 1

print("In season 1 there were {0} games in total:".format(total_games))
print("{0} were won by the player going first".format(won_by_first))
print("Of the {0} to have significantly differing rolls, {1} were won by the player with a better average roll".format(total_games-equivalent_luck, won_by_luck))
print("Of the {0} where players had significantly differing skill levels, {1} were won by the player with the higher skill level".format(total_games-equivalent_skill, won_by_higher_skill))
print("Of the {0} where players had significantly differing Elo ratings, {1} were won by the player with the higher Elo rating".format(total_games-equivalent_elo, won_by_higher_elo))
print("Of the {0} to have significantly differing experience, {1} were won by the player with more games played".format(total_games-equivalent_experience, won_by_experience))
print("Of the {0} played at a material imbalance, {1} were won by the player with the better selection".format(total_games-equivalent_selection, won_by_selection))
print("Of the {0} where costs differed significantly, {1} were won by the player with the lower average cost/move".format(total_games-equivalent_cost, won_by_lower_cost))
print("Of the {0} where the number of mistakes made differed, {1} were won by the player with fewer mistakes".format(total_games-equivalent_mistakes, won_by_fewer_mistakes))

print("Of the {0} where players missed, {1} were won by the player who didn't miss first".format(total_games-no_misses, won_by_first_miss))
print("Of the {0} where mistakes were made, {1} were won by the player who didn't make the first mistake".format(total_games-no_mistakes, won_by_first_mistake))
print("Of the {0} where the number of mistakes differed, {1} were won by the player who made fewer".format(total_games-equivalent_misses, won_by_miss_count))

fig, axs = plt.subplots(4,4, figsize = (16,16))
fig.suptitle("Season 1, {0} total games".format(total_games), bbox=dict(facecolor='0.75', edgecolor='black', boxstyle='round,pad=1'))

axs[0,0].pie([1,1,1], labels =["Correct", "Unclassified", "Incorrect"], shadow=True, autopct='%.2f%%', startangle=140)
axs[0,0].set_title("Example classifier", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[1,0].pie([won_by_luck, equivalent_luck, total_games-(won_by_luck + equivalent_luck)], labels =["luckier player won", "similar luck", "luckier player lost"], autopct='%.2f%%', shadow=True, startangle=140)
axs[1,0].set_title("Luck (avg roll)", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[2,0].pie([won_by_lower_cost, equivalent_cost, total_games-(won_by_lower_cost+equivalent_cost)], labels = ["lower cost player won", "similar costs", "higher cost player won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[2,0].set_title("Skill (avg cost)", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[3,0].pie([won_by_higher_skill, equivalent_skill, total_games-(won_by_higher_skill+equivalent_skill)], labels = ["higher skilled won", "similar skill", "lower skilled won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[3,0].set_title("Skill-points", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

# new column

axs[0,1].pie([won_by_selection, equivalent_selection, total_games-(won_by_selection+equivalent_selection)], labels = ["better selection won", "similar selection", "worse selection won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[0,1].set_title("Material", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[1,1].pie([won_by_higher_elo, equivalent_elo, total_games-(equivalent_elo + won_by_higher_skill)], labels =["higher Elo won", "equivalent Elo", "lower Elo won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[1,1].set_title("Elo", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))


axs[2,1].pie([won_by_fewer_mistakes, equivalent_mistakes, total_games-(won_by_fewer_mistakes + equivalent_mistakes)], labels = ["fewer mistakes won", "similar mistakes", "more mistakes won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[2,1].set_title("Mistakes made (cost > {0}*optimal)".format(mistake_threshold), bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[3,1].pie([won_by_first_miss, no_misses, total_games-(won_by_first_miss + no_misses)], labels =["didn't miss first, won", "no misses in game", "missed first, won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[3,1].set_title("First miss", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

# new column

axs[0,2].pie([won_by_first_mistake, no_mistakes, total_games-(no_mistakes + won_by_first_mistake)], labels = ["didn't make first mistake, won", "no mistakes", "made first mistake, won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[0,2].set_title("First mistake", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[1,2].pie([won_by_experience, equivalent_experience, total_games-(equivalent_experience + won_by_experience)], labels =["more experienced won", "equivalent experience", "less experienced won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[1,2].set_title("Games played", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[2,2].pie([won_by_miss_count, equivalent_misses, total_games-(equivalent_misses + won_by_miss_count)], labels =["fewer misses won", "equivalent misses", "more misses won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[2,2].set_title("Miss frequency", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[3,2].pie([won_by_total_cost, equivalent_cumulative_cost, total_games-(equivalent_cumulative_cost + won_by_total_cost)], labels =["lower total cost, won", "equivalent total cost", "higher total cost, won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[3,2].set_title("Total cost", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

# new column

axs[0,3].pie([won_by_first, 0, total_games-won_by_first], labels =["first mover won", "", "second mover won"], shadow=True, autopct=lambda p: '{:.2f}%'.format(p) if p > 0 else '', startangle=140)
axs[0,3].set_title("First move", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[1,3].pie([won_by_first_kill, 0, total_games-won_by_first_kill], labels =["first kill, won", "", "first kill, lost"], shadow=True, autopct=lambda p: '{:.2f}%'.format(p) if p > 0 else '', startangle=140)
axs[1,3].set_title("First kill", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[2,3].pie([won_by_first_major_mistake, no_major_mistakes, total_games-(won_by_first_major_mistake+no_major_mistakes)], labels = ["second major mistake, won", "no major mistakes", "first major mistake, won"], shadow=True, autopct='%.2f%%', startangle=140)
axs[2,3].set_title("First Major Mistake (cost > {0}*optimal)".format(major_mistake_threshold), bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[3,3].pie([won_by_fewer_major_mistakes, no_major_mistakes+equivalent_major_mistakes, total_games-(won_by_fewer_major_mistakes+no_major_mistakes+equivalent_major_mistakes)], labels = ["fewer major mistakes, won", "equal major mistakes", "made more major mistakes, won"], shadow=True, autopct='%.2f%%', startangle=140)
axs[3,3].set_title("Major mistakes made", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

#
#
# AGAIN, but for season 2
#
#

total_games = db.completed_games.count_documents({"winner":{"$exists":True}, "balance_code":"1.2"}) - 2 # dodgy games.
won_by_first = 0                # amount won by player going first
won_by_higher_skill = 0         # amount won by player with significantly higher skill (>skill_delta above at end) [0.5 if skill is within delta]
equivalent_skill = 0            # similar skill level
won_by_experience = 0           # amount won by player to have played more games
equivalent_experience = 0       # same games played
won_by_higher_elo = 0           # amount won by player with significantly higher elo (>elo_delta more at end) [0.5 if elo is within delta]
equivalent_elo = 0              # similar elo ratings
won_by_lower_cost = 0           # amount won by player with lower average cost/move
equivalent_cost = 0             # equivalent costs
won_by_fewer_mistakes = 0       # amount won by player with fewer mistakes (moves with cost/optimal > mistake_threshold)
equivalent_mistakes = 0         # games with equivalent mistakes
won_by_selection = 0            # amount won by player with material that should win if players are playing optimally
equivalent_selection = 0        # similar materials
won_by_luck = 0                 # amount won by player with significantly higher roll results (>luck_delta more at end) [0.5 if luck is within delta]
equivalent_luck = 0             # similar roll fortune
won_by_first_miss = 0           # amount won by the player who didn't miss first        
won_by_miss_count = 0           # amount won by the player who won less
equivalent_misses = 0
no_misses = 0                   
won_by_first_mistake = 0        # amount won by the player who didn't make the first mistake
no_mistakes = 0
won_by_total_cost = 0           # amount won by the player with the highest total cost
equivalent_cumulative_cost = 0  
won_by_first_kill = 0           # amount won by the player that first killed an opposing character
won_by_fewer_major_mistakes = 0 # amount won by the player to make fewer major mistakes
no_major_mistakes = 0
won_by_first_major_mistake = 0  # amount own by player who did not make the first major mistake
equivalent_major_mistakes = 0   # same number of major errors made


players_seen = []               # list of players seen. Used to calculate prior games played quickly

# Process S1 games
set_config("tango-2-3")
for g in db.completed_games.find({"winner":{"$exists":True}, "balance_code":"1.2"}).sort("start_date", pymongo.ASCENDING):
    p1_rolls = []
    p2_rolls = []
    p1_costs = []
    p2_costs = []
    p1_mistakes = 0
    p2_mistakes = 0
    p1_major_mistakes = 0
    p2_major_mistakes = 0
    p1_misses = 0
    p2_misses = 0
    first_death = 0
    first_miss = 0
    first_mistake = 0
    first_major_mistake = 0

    if g["_id"] == objectid.ObjectId("5eaaee2c684de5692fc01ef6") or g["_id"] == objectid.ObjectId("5ec108ef29108c1ba22cb375"):    # Ignore dodgy games.
        continue

    # Who went first and did they win?
    if g["Moves"][0][1] == str(g["winner"]):
        won_by_first += 1

    # who has played more games and did they win?
    p1_played = players_seen.count(g["usernames"][0])
    p2_played = players_seen.count(g["usernames"][1])
    players_seen += g["usernames"]
    if (p1_played > p2_played and g["winner"] == 1) or (p1_played < p2_played and g["winner"] == 2):
        won_by_experience += 1
    if p1_played == p2_played:
        equivalent_experience += 1

    # What material was used and which should win?
    pair1 = g["p1c1"][0] + g["p1c2"][0]
    pair2 = g["p2c1"][0] + g["p2c2"][0]
    if chars.index(pair1[0]) > chars.index(pair1[1]):
        pair1 = pair1[1]+pair1[0]
    if chars.index(pair2[0]) > chars.index(pair2[1]):
        pair2 = pair2[1]+pair2[0]

    if abs(tango_optimality[pairs.index(pair1)][pairs.index(pair2)] - 0.5) < optimality_delta:
        equivalent_selection += 1
    elif (g["winner"] == 1 and tango_optimality[pairs.index(pair1)][pairs.index(pair2)] > 0.5) or (g["winner"] == 2 and tango_optimality[pairs.index(pair1)][pairs.index(pair2)] < 0.5):
        won_by_selection += 1

    state = get_initial_state(g)
    for m in g["Moves"]:     # for every move made
        
        if first_death == 0:
            if state[1:9].count(0) > 6:
                first_death = 1
            elif state[10:18].count(0) > 6:
                first_death = 2

        if first_miss == 0 and was_a_miss(m, state):
            first_miss = int(m[1])

        # add the roll to the arrays
        rolls_in_move = []
        if m.count("_") == 1:
            if "skip" not in m:
                rolls_in_move += [int(m.split("_")[1])]
        else:
            rolls_in_move += [int(m.split("_")[2])]   # add second roll
            rolls_in_move += [int(m.split("_")[1].split("p")[0])]
        if m[1] == "1":
           p1_rolls += rolls_in_move
        else:
            p2_rolls += rolls_in_move 
        # add the costs to the arrays and update mistake count
        if m[1] == "1":
            if was_a_miss(m, state):
                p1_misses += 1                        
            p1_costs += [cost(state, pair1, m, s2data)]
            val, pos = cost(state, pair1, m, s2data, classify_mistake=True)
            if pos > 0:
                if (pos-val) / pos >= mistake_threshold:
                    p1_mistakes += 1
                    if first_mistake == 0:
                        first_mistake = 1
                if (pos-val) / pos >= major_mistake_threshold:
                    p1_major_mistakes += 1
                    if first_major_mistake == 0:
                        first_major_mistake = 1
        elif m[1] == "2":
            if was_a_miss(m, state):
                p2_misses += 1
            p2_costs += [cost(flip_state(state), pair2, m, s2data)]
            val, pos = cost(flip_state(state), pair2, m, s2data, classify_mistake=True)
            if pos > 0:
                if (pos-val) / pos >= mistake_threshold:
                    p2_mistakes += 1
                    if first_mistake == 0:
                        first_mistake = 2
                    if (pos-val) / pos >= major_mistake_threshold:
                        p2_major_mistakes += 1
                        if first_major_mistake == 0:
                            first_major_mistake = 2
        do_action(m, state)

    # luck check
    if len(p1_rolls) == 0:
        p1_rolls = [0]
    if len(p2_rolls) == 0:
        p2_rolls = [0]
    if np.average(p1_rolls) - np.average(p2_rolls) < luck_delta:
        # luck was similar enough to discount
        equivalent_luck += 1
    elif (g["winner"] == 1 and np.average(p1_rolls) > np.average(p2_rolls)) or (g["winner"] == 2 and np.average(p1_rolls) < np.average(p2_rolls)):
        won_by_luck += 1
    
    # skill check
    if len(g["skill_points_at_end"]) != 2:
        equivalent_skill += 1
    elif g["skill_points_at_end"][g["usernames"][0]] - g["skill_points_at_end"][g["usernames"][1]] < skill_delta:
        equivalent_skill += 1
    elif g["skill_points_at_end"][g["usernames"][0]] > g["skill_points_at_end"][g["usernames"][1]] and g["winner"] == 1:
        won_by_higher_skill += 1
    elif g["skill_points_at_end"][g["usernames"][0]] < g["skill_points_at_end"][g["usernames"][1]] and g["winner"] == 2:
        won_by_higher_skill += 1
    
    # Elo check
    if g["elo_scores_at_end"][g["usernames"][0]] - g["elo_scores_at_end"][g["usernames"][1]] < elo_delta:
        equivalent_elo += 1
    elif g["elo_scores_at_end"][g["usernames"][0]] > g["elo_scores_at_end"][g["usernames"][1]] and g["winner"] == 1:
        won_by_higher_elo += 1
    elif g["elo_scores_at_end"][g["usernames"][0]] < g["elo_scores_at_end"][g["usernames"][1]] and g["winner"] == 2:
        won_by_higher_elo += 1
    
    # average cost check
    if len(p1_costs) == 0 or len(p2_costs) == 0:
        equivalent_cost += 1 # no moves made by a player. Possible with M
    elif (np.average(p1_costs) < np.average(p2_costs) and g["winner"] == 1) or (np.average(p1_costs) > np.average(p2_costs) and g["winner"] == 2):
        won_by_lower_cost += 1
    elif np.average(p1_costs) == np.average(p2_costs):
        equivalent_cost += 1

    # total cost check
    if abs(sum(p1_costs) - sum(p2_costs)) < total_cost_delta:
        equivalent_cumulative_cost += 1
    elif (g["winner"] == 1 and sum(p1_costs) < sum(p2_costs)) or (g["winner"] == 2 and sum(p1_costs) > sum(p2_costs)):
        won_by_total_cost += 1

    # mistake check
    if (g["winner"] == 1 and p1_mistakes < p2_mistakes) or (g["winner"] == 2 and p1_mistakes > p2_mistakes):
        won_by_fewer_mistakes += 1
    if p1_mistakes == p2_mistakes:
        equivalent_mistakes += 1

    # first miss check
    if first_miss == 0:
        no_misses += 1
    elif first_miss != g["winner"]:
        won_by_first_miss += 1

    # first mistake check
    if first_mistake == 0:
        no_mistakes += 1
    elif first_mistake != g["winner"]:
        won_by_first_mistake += 1

    # misses check
    if p1_misses == p2_misses:
        equivalent_misses += 1
    elif (g["winner"] == 1 and p1_misses < p2_misses) or (g["winner"] == 2 and p1_misses > p2_misses):
        won_by_miss_count += 1

    # first kill check
    if first_miss != g["winner"] and first_death != 0:
        won_by_first_kill += 1

    # first major mistake check
    if first_major_mistake != g["winner"] and first_major_mistake != 0:
        won_by_first_major_mistake += 1
    
    # major mistake count check
    if (p1_major_mistakes > p2_major_mistakes and g["winner"] == 2) or (p1_major_mistakes < p2_major_mistakes and g["winner"] == 1):
        won_by_fewer_major_mistakes += 1
    if first_major_mistake == 0:
        no_major_mistakes += 1
    elif p1_major_mistakes == p2_major_mistakes:
        equivalent_major_mistakes += 1

print("In season 1 there were {0} games in total:".format(total_games))
print("{0} were won by the player going first".format(won_by_first))
print("Of the {0} to have significantly differing rolls, {1} were won by the player with a better average roll".format(total_games-equivalent_luck, won_by_luck))
print("Of the {0} where players had significantly differing skill levels, {1} were won by the player with the higher skill level".format(total_games-equivalent_skill, won_by_higher_skill))
print("Of the {0} where players had significantly differing Elo ratings, {1} were won by the player with the higher Elo rating".format(total_games-equivalent_elo, won_by_higher_elo))
print("Of the {0} to have significantly differing experience, {1} were won by the player with more games played".format(total_games-equivalent_experience, won_by_experience))
print("Of the {0} played at a material imbalance, {1} were won by the player with the better selection".format(total_games-equivalent_selection, won_by_selection))
print("Of the {0} where costs differed significantly, {1} were won by the player with the lower average cost/move".format(total_games-equivalent_cost, won_by_lower_cost))
print("Of the {0} where the number of mistakes made differed, {1} were won by the player with fewer mistakes".format(total_games-equivalent_mistakes, won_by_fewer_mistakes))

print("Of the {0} where players missed, {1} were won by the player who didn't miss first".format(total_games-no_misses, won_by_first_miss))
print("Of the {0} where mistakes were made, {1} were won by the player who didn't make the first mistake".format(total_games-no_mistakes, won_by_first_mistake))
print("Of the {0} where the number of mistakes differed, {1} were won by the player who made fewer".format(total_games-equivalent_misses, won_by_miss_count))

fig, axs = plt.subplots(4,4, figsize = (16,16))
fig.suptitle("Season 2, {0} total games".format(total_games), bbox=dict(facecolor='0.75', edgecolor='black', boxstyle='round,pad=1'))

axs[0,0].pie([1,1,1], labels =["Correct", "Unclassified", "Incorrect"], shadow=True, autopct='%.2f%%', startangle=140)
axs[0,0].set_title("Example classifier", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[1,0].pie([won_by_luck, equivalent_luck, total_games-(won_by_luck + equivalent_luck)], labels =["luckier player won", "similar luck", "luckier player lost"], autopct='%.2f%%', shadow=True, startangle=140)
axs[1,0].set_title("Luck (avg roll)", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[2,0].pie([won_by_lower_cost, equivalent_cost, total_games-(won_by_lower_cost+equivalent_cost)], labels = ["lower cost player won", "similar costs", "higher cost player won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[2,0].set_title("Skill (avg cost)", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[3,0].pie([won_by_higher_skill, equivalent_skill, total_games-(won_by_higher_skill+equivalent_skill)], labels = ["higher skilled won", "similar skill", "lower skilled won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[3,0].set_title("Skill-points", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

# new column

axs[0,1].pie([won_by_selection, equivalent_selection, total_games-(won_by_selection+equivalent_selection)], labels = ["better selection won", "similar selection", "worse selection won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[0,1].set_title("Material", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[1,1].pie([won_by_higher_elo, equivalent_elo, total_games-(equivalent_elo + won_by_higher_skill)], labels =["higher Elo won", "equivalent Elo", "lower Elo won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[1,1].set_title("Elo", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))


axs[2,1].pie([won_by_fewer_mistakes, equivalent_mistakes, total_games-(won_by_fewer_mistakes + equivalent_mistakes)], labels = ["fewer mistakes won", "similar mistakes", "more mistakes won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[2,1].set_title("Mistakes made (cost > {0}*optimal)".format(mistake_threshold), bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[3,1].pie([won_by_first_miss, no_misses, total_games-(won_by_first_miss + no_misses)], labels =["didn't miss first, won", "no misses in game", "missed first, won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[3,1].set_title("First miss", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

# new column

axs[0,2].pie([won_by_first_mistake, no_mistakes, total_games-(no_mistakes + won_by_first_mistake)], labels = ["didn't make first mistake, won", "no mistakes", "made first mistake, won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[0,2].set_title("First mistake", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[1,2].pie([won_by_experience, equivalent_experience, total_games-(equivalent_experience + won_by_experience)], labels =["more experienced won", "equivalent experience", "less experienced won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[1,2].set_title("Games played", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[2,2].pie([won_by_miss_count, equivalent_misses, total_games-(equivalent_misses + won_by_miss_count)], labels =["fewer misses won", "equivalent misses", "more misses won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[2,2].set_title("Miss frequency", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[3,2].pie([won_by_total_cost, equivalent_cumulative_cost, total_games-(equivalent_cumulative_cost + won_by_total_cost)], labels =["lower total cost, won", "equivalent total cost", "higher total cost, won"], autopct='%.2f%%',shadow=True, startangle=140)
axs[3,2].set_title("Total cost", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

# new column

axs[0,3].pie([won_by_first, 0, total_games-won_by_first], labels =["first mover won", "", "second mover won"], shadow=True, autopct=lambda p: '{:.2f}%'.format(p) if p > 0 else '', startangle=140)
axs[0,3].set_title("First move", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[1,3].pie([won_by_first_kill, 0, total_games-won_by_first_kill], labels =["first kill, won", "", "first kill, lost"], shadow=True, autopct=lambda p: '{:.2f}%'.format(p) if p > 0 else '', startangle=140)
axs[1,3].set_title("First kill", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[2,3].pie([won_by_first_major_mistake, no_major_mistakes, total_games-(won_by_first_major_mistake+no_major_mistakes)], labels = ["second major mistake, won", "no major mistakes", "first major mistake, won"], shadow=True, autopct='%.2f%%', startangle=140)
axs[2,3].set_title("First Major Mistake (cost > {0}*optimal)".format(major_mistake_threshold), bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

axs[3,3].pie([won_by_fewer_major_mistakes, no_major_mistakes+equivalent_major_mistakes, total_games-(won_by_fewer_major_mistakes+no_major_mistakes+equivalent_major_mistakes)], labels = ["fewer major mistakes, won", "equal major mistakes", "made more major mistakes, won"], shadow=True, autopct='%.2f%%', startangle=140)
axs[3,3].set_title("Major mistakes made", bbox=dict(facecolor='white', edgecolor='red', boxstyle='round'))

"""


total_games = db.completed_games.count_documents({"winner":{"$exists":True}, "balance_code":"1.2"}) - 2 # dodgy games.

won_by_first = 0                # amount won by player going first
won_by_higher_skill = 0         # amount won by player with significantly higher skill (>skill_delta above at end) [0.5 if skill is within delta]
equivalent_skill = 0            # similar skill level
won_by_experience = 0           # amount won by player to have played more games
equivalent_experience = 0       # same games played
won_by_higher_elo = 0           # amount won by player with significantly higher elo (>elo_delta more at end) [0.5 if elo is within delta]
equivalent_elo = 0              # similar elo ratings
won_by_lower_cost = 0           # amount won by player with lower average cost/move
equivalent_cost = 0             # equivalent costs
won_by_fewer_mistakes = 0       # amount won by player with fewer mistakes (moves with cost/optimal > mistake_threshold)
equivalent_mistakes = 0         # games with equivalent mistakes
won_by_selection = 0            # amount won by player with material that should win if players are playing optimally
equivalent_selection = 0        # similar materials
won_by_luck = 0                 # amount won by player with significantly higher roll results (>luck_delta more at end) [0.5 if luck is within delta]
equivalent_luck = 0             # similar roll fortune
won_by_first_miss = 0           # amount won by the player who didn't miss first        
no_misses = 0                   
won_by_first_mistake = 0        # amount won by the player who didn't make the first mistake
no_mistakes = 0

players_seen = []               # list of players seen. Used to calculate prior games played quickly

# Process S1 games
set_config("tango-2-3")
for g in db.completed_games.find({"winner":{"$exists":True}, "balance_code":"1.2"}):
    p1_rolls = []
    p2_rolls = []
    p1_costs = []
    p2_costs = []
    p1_mistakes = 0
    p2_mistakes = 0
    
    if g["_id"] == objectid.ObjectId("5eaaee2c684de5692fc01ef6") or g["_id"] == objectid.ObjectId("5ec108ef29108c1ba22cb375"):    # Ignore dodgy games.
        continue

    # Who went first and did they win?
    if g["Moves"][0][1] == str(g["winner"]):
        won_by_first += 1

    # who has played more games and did they win?
    p1_played = players_seen.count(g["usernames"][0])
    p2_played = players_seen.count(g["usernames"][1])
    players_seen += g["usernames"]
    if (p1_played > p2_played and g["winner"] == 1) or (p1_played < p2_played and g["winner"] == 2):
        won_by_experience += 1
    if p1_played == p2_played:
        equivalent_experience += 1

    # What material was used and which should win?
    pair1 = g["p1c1"][0] + g["p1c2"][0]
    pair2 = g["p2c1"][0] + g["p2c2"][0]
    if chars.index(pair1[0]) > chars.index(pair1[1]):
        pair1 = pair1[1]+pair1[0]
    if chars.index(pair2[0]) > chars.index(pair2[1]):
        pair2 = pair2[1]+pair2[0]

    if abs(beta_optimality[pairs.index(pair1)][pairs.index(pair2)] - 0.5) < optimality_delta:
        equivalent_selection += 1
    elif (g["winner"] == 1 and beta_optimality[pairs.index(pair1)][pairs.index(pair2)] > 0.5) or (g["winner"] == 2 and beta_optimality[pairs.index(pair1)][pairs.index(pair2)] < 0.5):
        won_by_selection += 1

    first_miss = 0
    first_mistake = 0
    state = get_initial_state(g)
    for m in g["Moves"]:     # for every move made
        
        if first_miss == 0 and was_a_miss(m, state):
            first_miss = int(m[1])

        # add the roll to the arrays
        rolls_in_move = []
        if m.count("_") == 1:
            if "skip" not in m:
                rolls_in_move += [int(m.split("_")[1])]
        else:
            rolls_in_move += [int(m.split("_")[2])]   # add second roll
            rolls_in_move += [int(m.split("_")[1].split("p")[0])]
        if m[1] == "1":
           p1_rolls += rolls_in_move
        else:
            p2_rolls += rolls_in_move 
        # add the costs to the arrays and update mistake count
        if m[1] == "1":                        
            p1_costs += [cost(state, pair1, m, s2data)]
            val, pos = cost(state, pair1, m, s2data, classify_mistake=True)
            if pos > 0:
                if (pos-val) / pos > mistake_threshold:
                    p1_mistakes += 1
                    if first_mistake == 0:
                        first_mistake = 1
        elif m[1] == "2":
            p2_costs += [cost(flip_state(state), pair2, m, s2data)]
            val, pos = cost(flip_state(state), pair2, m, s2data, classify_mistake=True)
            if pos > 0:
                if (pos-val) / pos > mistake_threshold:
                    p2_mistakes += 1
                    if first_mistake == 0:
                        first_mistake = 2
        do_action(m, state)

    # luck check
    if len(p1_rolls) == 0:
        p1_rolls = [0]
    if len(p2_rolls) == 0:
        p2_rolls = [0]
    if np.average(p1_rolls) - np.average(p2_rolls) < luck_delta:
        # luck was similar enough to discount
        equivalent_luck += 1
    elif (g["winner"] == 1 and np.average(p1_rolls) > np.average(p2_rolls)) or (g["winner"] == 2 and np.average(p1_rolls) < np.average(p2_rolls)):
        won_by_luck += 1
    
    # skill check
    if len(g["skill_points_at_end"]) != 2:
        equivalent_skill += 1
    elif g["skill_points_at_end"][g["usernames"][0]] - g["skill_points_at_end"][g["usernames"][1]] < skill_delta:
        equivalent_skill += 1
    elif g["skill_points_at_end"][g["usernames"][0]] > g["skill_points_at_end"][g["usernames"][1]] and g["winner"] == 1:
        won_by_higher_skill += 1
    elif g["skill_points_at_end"][g["usernames"][0]] < g["skill_points_at_end"][g["usernames"][1]] and g["winner"] == 2:
        won_by_higher_skill += 1
    
    # Elo check
    if g["elo_scores_at_end"][g["usernames"][0]] - g["elo_scores_at_end"][g["usernames"][1]] < elo_delta:
        equivalent_elo += 1
    elif g["elo_scores_at_end"][g["usernames"][0]] > g["elo_scores_at_end"][g["usernames"][1]] and g["winner"] == 1:
        won_by_higher_elo += 1
    elif g["elo_scores_at_end"][g["usernames"][0]] < g["elo_scores_at_end"][g["usernames"][1]] and g["winner"] == 2:
        won_by_higher_elo += 1
    
    # cost check
    if len(p1_costs) == 0 or len(p2_costs) == 0:
        equivalent_cost += 1 # no moves made by a player. Possible with M
    elif (np.average(p1_costs) < np.average(p2_costs) and g["winner"] == 1) or (np.average(p1_costs) > np.average(p2_costs) and g["winner"] == 2):
        won_by_lower_cost += 1
    elif np.average(p1_costs) == np.average(p2_costs):
        equivalent_cost += 1

    # mistake check
    if (g["winner"] == 1 and p1_mistakes < p2_mistakes) or (g["winner"] == 2 and p1_mistakes > p2_mistakes):
        won_by_fewer_mistakes += 1
    if p1_mistakes == p2_mistakes:
        equivalent_mistakes += 1

    # first miss check
    if first_miss == 0:
        no_misses += 1
    elif first_miss != g["winner"]:
        won_by_first_miss += 1

    # first mistake check
    if first_mistake == 0:
        no_mistakes += 1
    elif first_mistake != g["winner"]:
        won_by_first_mistake += 1

print("In season 2 there were {0} games in total:".format(total_games))
print("{0} were won by the player going first".format(won_by_first))
print("Of the {0} to have significantly differing rolls, {1} were won by the player with a better average roll".format(total_games-equivalent_luck, won_by_luck))
print("Of the {0} where players had significantly differing skill levels, {1} were won by the player with the higher skill level".format(total_games-equivalent_skill, won_by_higher_skill))
print("Of the {0} where players had significantly differing Elo ratings, {1} were won by the player with the higher Elo rating".format(total_games-equivalent_elo, won_by_higher_elo))
print("Of the {0} to have significantly differing experience, {1} were won by the player with more games played".format(total_games-equivalent_experience, won_by_experience))
print("Of the {0} played at a material imbalance, {1} were won by the player with the better selection".format(total_games-equivalent_selection, won_by_selection))
print("Of the {0} where costs differed significantly, {1} were won by the player with the lower average cost/move".format(total_games-equivalent_cost, won_by_lower_cost))
print("Of the {0} where the number of mistakes made differed, {1} were won by the player with fewer mistakes".format(total_games-equivalent_mistakes, won_by_fewer_mistakes))
print("Of the {0} where players missed, {1} were won by the player who didn't miss first".format(total_games-no_misses, won_by_first_miss))
print("Of the {0} where mistakes were made, {1} were won by the player who didn't make the first mistake".format(total_games-no_mistakes, won_by_first_mistake))



plt.figure(1)
fig, axs1 = plt.subplots(4,4)
axs1[0,0].pie([won_by_first, total_games-won_by_first], labels =["first mover won", "second mover won"], shadow=True, startangle=140)
plt.title("PopularitY of Programming Language\n" + "Worldwide, Oct 2017 compared to a year ago", bbox={'facecolor':'0.8', 'pad':5})




plt.tight_layout()

"""
plt.show()